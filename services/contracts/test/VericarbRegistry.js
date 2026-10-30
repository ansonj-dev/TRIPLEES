const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('VericarbRegistry', function () {
  async function fixture() {
    const [admin, issuer, owner, recipient, outsider, oracle, reviewer] = await ethers.getSigners();
    const Registry = await ethers.getContractFactory('VericarbRegistry');
    const registry = await Registry.deploy();
    const projectId = ethers.id('project-001');
    const batchId = ethers.id('batch-001');
    const evidenceHash = `0x${'12'.repeat(32)}`; // SHA-256-sized digest fixture.
    await registry.setRole(await registry.ISSUER_ROLE(), issuer.address, true);
    await registry.setRole(await registry.ORACLE_ROLE(), oracle.address, true);
    await registry.setRole(await registry.VERIFIER_ROLE(), reviewer.address, true);
    await registry.connect(issuer).registerProject(projectId, ethers.id('registry-ref'), ethers.id('methodology'), 2020, 2025);
    return { registry, admin, issuer, owner, recipient, outsider, oracle, reviewer, projectId, batchId, evidenceHash };
  }

  async function registerBatch(ctx, quantity = 1000) {
    return ctx.registry.connect(ctx.issuer).registerCreditBatch(ctx.batchId, ctx.projectId, ctx.owner.address, quantity, ctx.evidenceHash);
  }

  it('registers a project and a unique positive batch with traceable metadata', async function () {
    const ctx = await fixture();
    const project = await ctx.registry.getProject(ctx.projectId);
    expect(project.exists).to.equal(true);
    expect(project.methodologyHash).to.equal(ethers.id('methodology'));
    await expect(ctx.registry.connect(ctx.issuer).registerProject(ctx.projectId, ethers.ZeroHash, ethers.ZeroHash, 0, 0))
      .to.be.revertedWithCustomError(ctx.registry, 'DuplicateProject');
    await expect(ctx.registry.connect(ctx.issuer).registerProject(ethers.id('bad-vintage'), ethers.ZeroHash, ethers.ZeroHash, 2030, 2020))
      .to.be.revertedWithCustomError(ctx.registry, 'InvalidVintage');

    await expect(registerBatch(ctx))
      .to.emit(ctx.registry, 'BatchRegistered').withArgs(ctx.batchId, ctx.projectId, ctx.owner.address, 1000, ctx.evidenceHash, anyValue);
    const batch = await ctx.registry.getCreditBatch(ctx.batchId);
    expect(batch.quantityKg).to.equal(1000);
    expect(batch.state).to.equal(1); // Active
    expect(await ctx.registry.availableOf(ctx.batchId, ctx.owner.address)).to.equal(1000);
    await expect(registerBatch(ctx)).to.be.revertedWithCustomError(ctx.registry, 'DuplicateBatch');
    await expect(ctx.registry.connect(ctx.issuer).registerCreditBatch(ethers.id('zero'), ctx.projectId, ctx.owner.address, 0, ctx.evidenceHash))
      .to.be.revertedWithCustomError(ctx.registry, 'InvalidAmount');
    await expect(ctx.registry.connect(ctx.issuer).registerCreditBatch(ethers.id('missing-project'), ethers.id('missing'), ctx.owner.address, 1, ctx.evidenceHash))
      .to.be.revertedWithCustomError(ctx.registry, 'ProjectNotFound');
  });

  it('enforces issuer, oracle, and reviewer role boundaries', async function () {
    const ctx = await fixture();
    await expect(ctx.registry.connect(ctx.outsider).registerProject(ethers.id('x'), ethers.ZeroHash, ethers.ZeroHash, 0, 0))
      .to.be.revertedWithCustomError(ctx.registry, 'Unauthorized');
    await expect(ctx.registry.connect(ctx.outsider).registerCreditBatch(ctx.batchId, ctx.projectId, ctx.owner.address, 10, ctx.evidenceHash))
      .to.be.revertedWithCustomError(ctx.registry, 'Unauthorized');
    await registerBatch(ctx);
    await expect(ctx.registry.connect(ctx.outsider).markAtRisk(ctx.batchId, ethers.id('risk')))
      .to.be.revertedWithCustomError(ctx.registry, 'Unauthorized');
    await expect(ctx.registry.connect(ctx.outsider).recordReviewDecision(ctx.batchId, 1, ethers.id('decision')))
      .to.be.revertedWithCustomError(ctx.registry, 'Unauthorized');
  });

  it('anchors a unique SHA-256 evidence reference and returns its submitter and timestamp', async function () {
    const ctx = await fixture();
    await registerBatch(ctx);
    const evidenceId = ethers.id('evidence-001');
    const evidenceTypeHash = ethers.id('document');
    await expect(ctx.registry.connect(ctx.issuer).anchorEvidence(evidenceId, ctx.projectId, ctx.batchId, ctx.evidenceHash, evidenceTypeHash))
      .to.emit(ctx.registry, 'EvidenceAnchored').withArgs(evidenceId, ctx.projectId, ctx.batchId, ctx.evidenceHash, evidenceTypeHash, ctx.issuer.address, anyValue);
    const anchor = await ctx.registry.getEvidenceAnchor(evidenceId);
    expect(anchor.sha256Hash).to.equal(ctx.evidenceHash);
    expect(anchor.submitter).to.equal(ctx.issuer.address);
    await expect(ctx.registry.connect(ctx.issuer).anchorEvidence(evidenceId, ctx.projectId, ctx.batchId, ctx.evidenceHash, evidenceTypeHash))
      .to.be.revertedWithCustomError(ctx.registry, 'DuplicateEvidence');
    expect((await ctx.registry.getBatchHistory(ctx.batchId)).length).to.equal(2);
  });

  it('supports transfers and partial/full retirement without balance reuse', async function () {
    const ctx = await fixture();
    await registerBatch(ctx);
    await expect(ctx.registry.connect(ctx.owner).transfer(ctx.batchId, ctx.recipient.address, 400))
      .to.emit(ctx.registry, 'CreditTransferred');
    expect(await ctx.registry.availableOf(ctx.batchId, ctx.owner.address)).to.equal(600);
    expect(await ctx.registry.availableOf(ctx.batchId, ctx.recipient.address)).to.equal(400);
    await expect(ctx.registry.connect(ctx.owner).transfer(ctx.batchId, ctx.recipient.address, 601))
      .to.be.revertedWithCustomError(ctx.registry, 'InsufficientBalance');
    await expect(ctx.registry.connect(ctx.owner).retire(ctx.batchId, 601, ethers.id('retire-too-much')))
      .to.be.revertedWithCustomError(ctx.registry, 'InsufficientBalance');
    await ctx.registry.connect(ctx.owner).retire(ctx.batchId, 600, ethers.id('retire-owner'));
    await ctx.registry.connect(ctx.recipient).retire(ctx.batchId, 400, ethers.id('retire-recipient'));
    expect((await ctx.registry.getCreditBatch(ctx.batchId)).state).to.equal(5); // Retired
    expect((await ctx.registry.getCreditBatch(ctx.batchId)).retiredKg).to.equal(1000);
    await expect(ctx.registry.connect(ctx.owner).transfer(ctx.batchId, ctx.recipient.address, 1))
      .to.be.revertedWithCustomError(ctx.registry, 'InvalidState');
    expect((await ctx.registry.getBatchHistory(ctx.batchId)).length).to.equal(4);
  });

  it('records risk, review decisions, and preserves retired history through reversal', async function () {
    const ctx = await fixture();
    await registerBatch(ctx);
    await ctx.registry.connect(ctx.owner).retire(ctx.batchId, 250, ethers.id('retire-before-risk'));
    await ctx.registry.connect(ctx.oracle).markAtRisk(ctx.batchId, ethers.id('synthetic-risk'));
    await expect(ctx.registry.connect(ctx.oracle).openReview(ctx.batchId, ethers.id('review-opened')))
      .to.emit(ctx.registry, 'ReviewDecisionRecorded');
    await expect(ctx.registry.connect(ctx.reviewer).recordReviewDecision(ctx.batchId, 1, ethers.id('reversal-confirmed')))
      .to.emit(ctx.registry, 'ReviewDecisionRecorded');
    const batch = await ctx.registry.getCreditBatch(ctx.batchId);
    expect(batch.state).to.equal(4); // Reversed
    expect(batch.retiredKg).to.equal(250);
    await expect(ctx.registry.connect(ctx.owner).transfer(ctx.batchId, ctx.recipient.address, 1))
      .to.be.revertedWithCustomError(ctx.registry, 'InvalidState');
    expect((await ctx.registry.getBatchHistory(ctx.batchId)).length).to.equal(5);
  });
});

const anyValue = (value) => typeof value === 'bigint';
