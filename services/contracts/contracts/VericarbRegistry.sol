// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Hash-and-lifecycle registry. On-chain records do not prove a physical climate outcome.
contract VericarbRegistry {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");

    enum State { None, Active, AtRisk, InReview, Reversed, Retired }
    enum ReviewDecision { RequestMoreEvidence, ConfirmReversal, RejectReversal }

    struct Project {
        bool exists;
        bytes32 registryRefHash;
        bytes32 methodologyHash;
        uint16 vintageStartYear;
        uint16 vintageEndYear;
        address registrar;
        uint64 registeredAt;
    }

    struct Batch {
        bytes32 projectId;
        uint256 quantityKg;
        uint256 retiredKg;
        bytes32 evidenceHash;
        State state;
        address issuer;
        uint64 registeredAt;
    }

    struct EvidenceAnchor {
        bool exists;
        bytes32 projectId;
        bytes32 batchId;
        bytes32 sha256Hash;
        bytes32 evidenceTypeHash;
        address submitter;
        uint64 anchoredAt;
    }

    struct LifecycleEvent {
        bytes32 eventType;
        bytes32 dataHash;
        address actor;
        uint256 quantityKg;
        uint64 timestamp;
    }

    address public admin;
    mapping(bytes32 => mapping(address => bool)) private roles;
    mapping(bytes32 => Project) private projects;
    mapping(bytes32 => Batch) private batches;
    mapping(bytes32 => mapping(address => uint256)) public balances;
    mapping(bytes32 => EvidenceAnchor) private evidenceAnchors;
    mapping(bytes32 => LifecycleEvent[]) private batchHistory;

    event RoleUpdated(bytes32 indexed role, address indexed account, bool enabled);
    event ProjectRegistered(bytes32 indexed projectId, bytes32 registryRefHash, bytes32 methodologyHash, uint16 vintageStartYear, uint16 vintageEndYear, address indexed registrar, uint64 timestamp);
    event BatchRegistered(bytes32 indexed batchId, bytes32 indexed projectId, address indexed owner, uint256 quantityKg, bytes32 evidenceHash, uint64 timestamp);
    event EvidenceAnchored(bytes32 indexed evidenceId, bytes32 indexed projectId, bytes32 indexed batchId, bytes32 sha256Hash, bytes32 evidenceTypeHash, address submitter, uint64 timestamp);
    event CreditTransferred(bytes32 indexed batchId, address indexed from, address indexed to, uint256 quantityKg, uint64 timestamp);
    event CreditRetired(bytes32 indexed batchId, address indexed owner, uint256 quantityKg, bytes32 indexed retirementRef, uint64 timestamp);
    event BatchAtRisk(bytes32 indexed batchId, bytes32 reasonHash, uint64 timestamp);
    event ReviewDecisionRecorded(bytes32 indexed batchId, ReviewDecision decision, bytes32 reasonHash, address indexed reviewer, uint64 timestamp);

    error Unauthorized();
    error InvalidAddress();
    error InvalidAmount();
    error DuplicateProject();
    error ProjectNotFound();
    error DuplicateBatch();
    error BatchNotFound();
    error DuplicateEvidence();
    error EvidenceNotFound();
    error InsufficientBalance();
    error InvalidState();
    error InvalidHash();
    error InvalidVintage();

    modifier onlyAdmin() { if (msg.sender != admin) revert Unauthorized(); _; }
    modifier onlyRole(bytes32 role) { if (!roles[role][msg.sender]) revert Unauthorized(); _; }

    constructor() {
        admin = msg.sender;
        roles[ISSUER_ROLE][msg.sender] = true;
        roles[ORACLE_ROLE][msg.sender] = true;
        roles[VERIFIER_ROLE][msg.sender] = true;
    }

    function setRole(bytes32 role, address account, bool enabled) external onlyAdmin {
        if (account == address(0)) revert InvalidAddress();
        if (role != ISSUER_ROLE && role != ORACLE_ROLE && role != VERIFIER_ROLE) revert InvalidState();
        roles[role][account] = enabled;
        emit RoleUpdated(role, account, enabled);
    }

    function hasRole(bytes32 role, address account) external view returns (bool) { return roles[role][account]; }

    function registerProject(
        bytes32 projectId,
        bytes32 registryRefHash,
        bytes32 methodologyHash,
        uint16 vintageStartYear,
        uint16 vintageEndYear
    ) external onlyRole(ISSUER_ROLE) {
        if (projectId == bytes32(0)) revert InvalidHash();
        if (projects[projectId].exists) revert DuplicateProject();
        if (vintageStartYear != 0 && vintageEndYear != 0 && vintageEndYear < vintageStartYear) revert InvalidVintage();
        uint64 nowAt = uint64(block.timestamp);
        projects[projectId] = Project(true, registryRefHash, methodologyHash, vintageStartYear, vintageEndYear, msg.sender, nowAt);
        emit ProjectRegistered(projectId, registryRefHash, methodologyHash, vintageStartYear, vintageEndYear, msg.sender, nowAt);
    }

    function getProject(bytes32 projectId) external view returns (Project memory) {
        if (!projects[projectId].exists) revert ProjectNotFound();
        return projects[projectId];
    }

    function registerCreditBatch(
        bytes32 batchId,
        bytes32 projectId,
        address owner,
        uint256 quantityKg,
        bytes32 evidenceHash
    ) external onlyRole(ISSUER_ROLE) {
        if (batchId == bytes32(0) || batches[batchId].state != State.None) revert DuplicateBatch();
        if (!projects[projectId].exists) revert ProjectNotFound();
        if (owner == address(0)) revert InvalidAddress();
        if (quantityKg == 0) revert InvalidAmount();
        if (evidenceHash == bytes32(0)) revert InvalidHash();
        uint64 nowAt = uint64(block.timestamp);
        batches[batchId] = Batch(projectId, quantityKg, 0, evidenceHash, State.Active, msg.sender, nowAt);
        balances[batchId][owner] = quantityKg;
        emit BatchRegistered(batchId, projectId, owner, quantityKg, evidenceHash, nowAt);
        _append(batchId, keccak256("BATCH_REGISTERED"), evidenceHash, quantityKg, nowAt);
    }

    function getCreditBatch(bytes32 batchId) external view returns (Batch memory) {
        if (batches[batchId].state == State.None) revert BatchNotFound();
        return batches[batchId];
    }

    function anchorEvidence(
        bytes32 evidenceId,
        bytes32 projectId,
        bytes32 batchId,
        bytes32 sha256Hash,
        bytes32 evidenceTypeHash
    ) external onlyRole(ISSUER_ROLE) {
        if (evidenceId == bytes32(0) || sha256Hash == bytes32(0) || evidenceTypeHash == bytes32(0)) revert InvalidHash();
        if (evidenceAnchors[evidenceId].exists) revert DuplicateEvidence();
        if (projectId != bytes32(0) && !projects[projectId].exists) revert ProjectNotFound();
        if (batchId != bytes32(0) && batches[batchId].state == State.None) revert BatchNotFound();
        if (projectId == bytes32(0) && batchId == bytes32(0)) revert InvalidState();
        uint64 nowAt = uint64(block.timestamp);
        evidenceAnchors[evidenceId] = EvidenceAnchor(true, projectId, batchId, sha256Hash, evidenceTypeHash, msg.sender, nowAt);
        emit EvidenceAnchored(evidenceId, projectId, batchId, sha256Hash, evidenceTypeHash, msg.sender, nowAt);
        if (batchId != bytes32(0)) _append(batchId, keccak256("EVIDENCE_ANCHORED"), sha256Hash, 0, nowAt);
    }

    function getEvidenceAnchor(bytes32 evidenceId) external view returns (EvidenceAnchor memory) {
        if (!evidenceAnchors[evidenceId].exists) revert EvidenceNotFound();
        return evidenceAnchors[evidenceId];
    }

    function transfer(bytes32 batchId, address to, uint256 quantityKg) external {
        Batch storage batch = batches[batchId];
        if (batch.state == State.None) revert BatchNotFound();
        if (to == address(0)) revert InvalidAddress();
        if (batch.state != State.Active) revert InvalidState();
        if (quantityKg == 0) revert InvalidAmount();
        uint256 available = balances[batchId][msg.sender];
        if (available < quantityKg) revert InsufficientBalance();
        balances[batchId][msg.sender] = available - quantityKg;
        balances[batchId][to] += quantityKg;
        uint64 nowAt = uint64(block.timestamp);
        emit CreditTransferred(batchId, msg.sender, to, quantityKg, nowAt);
        _append(batchId, keccak256("CREDIT_TRANSFERRED"), keccak256(abi.encode(msg.sender, to)), quantityKg, nowAt);
    }

    function retire(bytes32 batchId, uint256 quantityKg, bytes32 retirementRef) external {
        Batch storage batch = batches[batchId];
        if (batch.state == State.None) revert BatchNotFound();
        if (batch.state != State.Active) revert InvalidState();
        if (quantityKg == 0) revert InvalidAmount();
        if (retirementRef == bytes32(0)) revert InvalidHash();
        uint256 available = balances[batchId][msg.sender];
        if (available < quantityKg) revert InsufficientBalance();
        balances[batchId][msg.sender] = available - quantityKg;
        batch.retiredKg += quantityKg;
        if (batch.retiredKg == batch.quantityKg) batch.state = State.Retired;
        uint64 nowAt = uint64(block.timestamp);
        emit CreditRetired(batchId, msg.sender, quantityKg, retirementRef, nowAt);
        _append(batchId, keccak256("CREDIT_RETIRED"), retirementRef, quantityKg, nowAt);
    }

    function markAtRisk(bytes32 batchId, bytes32 reasonHash) external onlyRole(ORACLE_ROLE) {
        Batch storage batch = batches[batchId];
        if (batch.state == State.None) revert BatchNotFound();
        if (batch.state != State.Active || reasonHash == bytes32(0)) revert InvalidState();
        batch.state = State.AtRisk;
        uint64 nowAt = uint64(block.timestamp);
        emit BatchAtRisk(batchId, reasonHash, nowAt);
        _append(batchId, keccak256("BATCH_AT_RISK"), reasonHash, 0, nowAt);
    }

    function openReview(bytes32 batchId, bytes32 reasonHash) external onlyRole(ORACLE_ROLE) {
        Batch storage batch = batches[batchId];
        if (batch.state == State.None) revert BatchNotFound();
        if (batch.state != State.AtRisk || reasonHash == bytes32(0)) revert InvalidState();
        batch.state = State.InReview;
        uint64 nowAt = uint64(block.timestamp);
        emit ReviewDecisionRecorded(batchId, ReviewDecision.RequestMoreEvidence, reasonHash, msg.sender, nowAt);
        _append(batchId, keccak256("REVIEW_OPENED"), reasonHash, 0, nowAt);
    }

    function recordReviewDecision(bytes32 batchId, ReviewDecision decision, bytes32 reasonHash) external onlyRole(VERIFIER_ROLE) {
        Batch storage batch = batches[batchId];
        if (batch.state == State.None) revert BatchNotFound();
        if (batch.state != State.InReview || reasonHash == bytes32(0)) revert InvalidState();
        if (decision == ReviewDecision.ConfirmReversal) batch.state = State.Reversed;
        else if (decision == ReviewDecision.RejectReversal) batch.state = batch.retiredKg == batch.quantityKg ? State.Retired : State.Active;
        else batch.state = State.AtRisk;
        uint64 nowAt = uint64(block.timestamp);
        emit ReviewDecisionRecorded(batchId, decision, reasonHash, msg.sender, nowAt);
        _append(batchId, keccak256("REVIEW_DECISION"), reasonHash, uint256(decision), nowAt);
    }

    function availableOf(bytes32 batchId, address owner) external view returns (uint256) { return balances[batchId][owner]; }

    function getBatchHistory(bytes32 batchId) external view returns (LifecycleEvent[] memory) {
        if (batches[batchId].state == State.None) revert BatchNotFound();
        return batchHistory[batchId];
    }

    function _append(bytes32 batchId, bytes32 eventType, bytes32 dataHash, uint256 quantityKg, uint64 timestamp) private {
        batchHistory[batchId].push(LifecycleEvent(eventType, dataHash, msg.sender, quantityKg, timestamp));
    }
}
