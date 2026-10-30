const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('InvestigationReportAnchorRegistry', function () {
  it('stores an immutable report hash and minimal version metadata', async function () {
    const [admin, anchorer] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory('InvestigationReportAnchorRegistry');
    const registry = await Factory.deploy();
    const anchorId = ethers.id('opaque-anchor-reference');
    const sha256Hash = `0x${'ab'.repeat(32)}`;
    await registry.setAnchorer(anchorer.address, true);

    await expect(registry.connect(anchorer).anchorReport(anchorId, sha256Hash, 3))
      .to.emit(registry, 'ReportAnchored')
      .withArgs(anchorId, sha256Hash, 3, anchorer.address, anyValue);
    const record = await registry.getReportAnchor(anchorId);
    expect(record.exists).to.equal(true);
    expect(record.sha256Hash).to.equal(sha256Hash);
    expect(record.version).to.equal(3);
    expect(record.anchorer).to.equal(anchorer.address);
    await expect(registry.connect(anchorer).anchorReport(anchorId, sha256Hash, 3))
      .to.be.revertedWithCustomError(registry, 'DuplicateAnchor');
    await expect(registry.connect(anchorer).anchorReport(ethers.id('other'), sha256Hash, 0))
      .to.be.revertedWithCustomError(registry, 'InvalidCommitment');
    expect(await registry.admin()).to.equal(admin.address);
  });

  it('restricts anchor submission and role administration', async function () {
    const [admin, outsider] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory('InvestigationReportAnchorRegistry');
    const registry = await Factory.deploy();
    await expect(registry.connect(outsider).anchorReport(ethers.id('id'), ethers.id('hash'), 1))
      .to.be.revertedWithCustomError(registry, 'Unauthorized');
    await expect(registry.connect(outsider).setAnchorer(outsider.address, true))
      .to.be.revertedWithCustomError(registry, 'Unauthorized');
    await expect(registry.setAnchorer(ethers.ZeroAddress, true))
      .to.be.revertedWithCustomError(registry, 'InvalidAddress');
    expect(await registry.hasRole(await registry.ANCHORER_ROLE(), admin.address)).to.equal(true);
  });
});

const anyValue = (value) => typeof value === 'bigint';
