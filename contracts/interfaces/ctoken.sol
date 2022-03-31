// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;

import "./comptroller.sol";

/**
 * @title Compound's InterestRateModel Interface
 * @author Compound
 */
interface InterestRateModel {
    /**
     * @dev Calculates the current borrow interest rate per block
     * @param cash The total amount of cash the market has
     * @param borrows The total amount of borrows the market has outstanding
     * @param reserves The total amnount of reserves the market has
     * @return The borrow rate per block (as a percentage, and scaled by 1e18)
     */
    function getBorrowRate(
        uint256 cash,
        uint256 borrows,
        uint256 reserves
    ) external view returns (uint256);

    /**
     * @dev Calculates the current supply interest rate per block
     * @param cash The total amount of cash the market has
     * @param borrows The total amount of borrows the market has outstanding
     * @param reserves The total amnount of reserves the market has
     * @param reserveFactorMantissa The current reserve factor the market has
     * @return The supply rate per block (as a percentage, and scaled by 1e18)
     */
    function getSupplyRate(
        uint256 cash,
        uint256 borrows,
        uint256 reserves,
        uint256 reserveFactorMantissa
    ) external view returns (uint256);
}

interface ICTokenStorage {
    /**
     * @dev Container for borrow balance information
     * @member principal Total balance (with accrued interest), after applying the most recent balance-changing action
     * @member interestIndex Global borrowIndex as of the most recent balance-changing action
     */
    struct BorrowSnapshot {
        uint256 principal;
        uint256 interestIndex;
    }
}

interface ICToken is ICTokenStorage {
    /*** Market Events ***/

    /**
     * @dev Event emitted when interest is accrued
     */
    event AccrueInterest(
        uint256 cashPrior,
        uint256 interestAccumulated,
        uint256 borrowIndex,
        uint256 totalBorrows
    );

    /**
     * @dev Event emitted when tokens are minted
     */
    event Mint(address minter, uint256 mintAmount, uint256 mintTokens);

    /**
     * @dev Event emitted when tokens are redeemed
     */
    event Redeem(address redeemer, uint256 redeemAmount, uint256 redeemTokens);

    /**
     * @dev Event emitted when underlying is borrowed
     */
    event Borrow(
        address borrower,
        uint256 borrowAmount,
        uint256 accountBorrows,
        uint256 totalBorrows
    );

    /**
     * @dev Event emitted when a borrow is repaid
     */
    event RepayBorrow(
        address payer,
        address borrower,
        uint256 repayAmount,
        uint256 accountBorrows,
        uint256 totalBorrows
    );

    /**
     * @dev Event emitted when a borrow is liquidated
     */
    event LiquidateBorrow(
        address liquidator,
        address borrower,
        uint256 repayAmount,
        address cTokenCollateral,
        uint256 seizeTokens
    );

    /*** Admin Events ***/

    /**
     * @dev Event emitted when pendingAdmin is changed
     */
    event NewPendingAdmin(address oldPendingAdmin, address newPendingAdmin);

    /**
     * @dev Event emitted when pendingAdmin is accepted, which means admin is updated
     */
    event NewAdmin(address oldAdmin, address newAdmin);

    /**
     * @dev Event emitted when comptroller is changed
     */
    event NewComptroller(
        IComptroller oldComptroller,
        IComptroller newComptroller
    );

    /**
     * @dev Event emitted when interestRateModel is changed
     */
    event NewMarketInterestRateModel(
        InterestRateModel oldInterestRateModel,
        InterestRateModel newInterestRateModel
    );

    /**
     * @dev Event emitted when the reserve factor is changed
     */
    event NewReserveFactor(
        uint256 oldReserveFactorMantissa,
        uint256 newReserveFactorMantissa
    );

    /**
     * @dev Event emitted when the reserves are added
     */
    event ReservesAdded(
        address benefactor,
        uint256 addAmount,
        uint256 newTotalReserves
    );

    /**
     * @dev Event emitted when the reserves are reduced
     */
    event ReservesReduced(
        address admin,
        uint256 reduceAmount,
        uint256 newTotalReserves
    );

    /**
     * @dev EIP20 Transfer event
     */
    event Transfer(address indexed from, address indexed to, uint256 amount);

    /**
     * @dev EIP20 Approval event
     */
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 amount
    );

    /**
     * @dev Failure event
     */
    event Failure(uint256 error, uint256 info, uint256 detail);

    /*** User Interface ***/
    function totalBorrows() external view returns (uint256);

    function totalReserves() external view returns (uint256);

    function totalSupply() external view returns (uint256);

    function transfer(address dst, uint256 amount) external returns (bool);

    function transferFrom(
        address src,
        address dst,
        uint256 amount
    ) external returns (bool);

    function approve(address spender, uint256 amount) external returns (bool);

    function allowance(address owner, address spender)
        external
        view
        returns (uint256);

    function balanceOf(address owner) external view returns (uint256);

    function balanceOfUnderlying(address owner) external returns (uint256);

    function getAccountSnapshot(address account)
        external
        view
        returns (
            uint256,
            uint256,
            uint256,
            uint256
        );

    function borrowRatePerBlock() external view returns (uint256);

    function supplyRatePerBlock() external view returns (uint256);

    function totalBorrowsCurrent() external returns (uint256);

    function borrowBalanceCurrent(address account) external returns (uint256);

    function borrowBalanceStored(address account)
        external
        view
        returns (uint256);

    function exchangeRateCurrent() external returns (uint256);

    function exchangeRateStored() external view returns (uint256);

    function getCash() external view returns (uint256);

    function accrueInterest() external returns (uint256);

    function seize(
        address liquidator,
        address borrower,
        uint256 seizeTokens
    ) external returns (uint256);

    /*** CCap Interface ***/

    function totalCollateralTokens() external view returns (uint256);

    function accountCollateralTokens(address account)
        external
        view
        returns (uint256);

    function isCollateralTokenInit(address account)
        external
        view
        returns (bool);

    function collateralCap() external view returns (uint256);

    /*** Admin Functions ***/

    function _setPendingAdmin(address payable newPendingAdmin)
        external
        returns (uint256);

    function _acceptAdmin() external returns (uint256);

    function _setComptroller(IComptroller newComptroller)
        external
        returns (uint256);

    function _setReserveFactor(uint256 newReserveFactorMantissa)
        external
        returns (uint256);

    function _reduceReserves(uint256 reduceAmount) external returns (uint256);

    function _setInterestRateModel(InterestRateModel newInterestRateModel)
        external
        returns (uint256);
}

interface ICTokenErc20 is ICToken {
    /*** User Interface ***/

    function mint(uint256 mintAmount) external returns (uint256);

    function redeem(uint256 redeemTokens) external returns (uint256);

    function redeemUnderlying(uint256 redeemAmount) external returns (uint256);

    function borrow(uint256 borrowAmount) external returns (uint256);

    function repayBorrow(uint256 repayAmount) external returns (uint256);

    function liquidateBorrow(
        address borrower,
        uint256 repayAmount,
        ICToken cTokenCollateral
    ) external returns (uint256);

    /*** Admin Functions ***/

    function _addReserves(uint256 addAmount) external returns (uint256);
}

interface ICCapableErc20 {
    /*** User Interface ***/

    function mint(uint256 mintAmount) external returns (uint256);

    function redeem(uint256 redeemTokens) external returns (uint256);

    function redeemUnderlying(uint256 redeemAmount) external returns (uint256);

    function borrow(uint256 borrowAmount) external returns (uint256);

    function repayBorrow(uint256 repayAmount) external returns (uint256);

    function liquidateBorrow(
        address borrower,
        uint256 repayAmount,
        ICToken cTokenCollateral
    ) external returns (uint256);

    function gulp() external;

    /*** Admin Functions ***/

    function _addReserves(uint256 addAmount) external returns (uint256);
}

interface CCollateralCapStorage {
    /**
     * @notice Total number of tokens used as collateral in circulation.
     */
    // uint256 public totalCollateralTokens;
    function totalCollateralTokens() external view returns (uint256);

    /**
     * @notice Record of token balances which could be treated as collateral for each account.
     *         If collateral cap is not set, the value should be equal to accountTokens.
     */
    // mapping(address => uint256) public accountCollateralTokens;
    function accountCollateralTokens(address account)
        external
        view
        returns (uint256);

    /**
     * @notice Check if accountCollateralTokens have been initialized.
     */
    // mapping(address => bool) public isCollateralTokenInit;
    function isCollateralTokenInit(address account)
        external
        view
        returns (bool);

    /**
     * @notice Collateral cap for this CToken, zero for no cap.
     */
    // uint256 public collateralCap;
    function collateralCap() external view returns (uint256);
}
