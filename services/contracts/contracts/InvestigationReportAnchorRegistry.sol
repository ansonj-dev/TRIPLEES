// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @notice Append-only SHA-256 commitments for off-chain investigation reports.
/// @dev Report content, findings, project details, and personal data are never stored here.
contract InvestigationReportAnchorRegistry {
    bytes32 public constant ANCHORER_ROLE = keccak256("ANCHORER_ROLE");

    struct ReportAnchor {
        bool exists;
        bytes32 sha256Hash;
        uint32 version;
        address anchorer;
        uint64 anchoredAt;
    }

    address public admin;
    mapping(address => bool) private anchorers;
    mapping(bytes32 => ReportAnchor) private reportAnchors;

    event AnchorerUpdated(address indexed account, bool enabled);
    event ReportAnchored(bytes32 indexed anchorId, bytes32 indexed sha256Hash, uint32 version, address indexed anchorer, uint64 anchoredAt);

    error Unauthorized();
    error InvalidAddress();
    error InvalidCommitment();
    error DuplicateAnchor();
    error AnchorNotFound();

    modifier onlyAdmin() {
        if (msg.sender != admin) revert Unauthorized();
        _;
    }

    modifier onlyAnchorer() {
        if (!anchorers[msg.sender]) revert Unauthorized();
        _;
    }

    constructor() {
        admin = msg.sender;
        anchorers[msg.sender] = true;
    }

    function setAnchorer(address account, bool enabled) external onlyAdmin {
        if (account == address(0)) revert InvalidAddress();
        anchorers[account] = enabled;
        emit AnchorerUpdated(account, enabled);
    }

    function hasRole(bytes32 role, address account) external view returns (bool) {
        return role == ANCHORER_ROLE && anchorers[account];
    }

    function anchorReport(bytes32 anchorId, bytes32 sha256Hash, uint32 version) external onlyAnchorer {
        if (anchorId == bytes32(0) || sha256Hash == bytes32(0) || version == 0) revert InvalidCommitment();
        if (reportAnchors[anchorId].exists) revert DuplicateAnchor();
        uint64 anchoredAt = uint64(block.timestamp);
        reportAnchors[anchorId] = ReportAnchor(true, sha256Hash, version, msg.sender, anchoredAt);
        emit ReportAnchored(anchorId, sha256Hash, version, msg.sender, anchoredAt);
    }

    function getReportAnchor(bytes32 anchorId) external view returns (ReportAnchor memory) {
        if (!reportAnchors[anchorId].exists) revert AnchorNotFound();
        return reportAnchors[anchorId];
    }

    function isAnchored(bytes32 anchorId) external view returns (bool) {
        return reportAnchors[anchorId].exists;
    }
}
