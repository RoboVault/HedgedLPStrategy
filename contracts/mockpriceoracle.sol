// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;
import "./interfaces/comppriceoracle.sol";

contract MockPriceOracle {
    bool public constant isPriceOracle = true;
    mapping(address => uint256) public prices;
    ICompPriceOracle oldOracle;

    constructor(address _oldOracle) public {
        oldOracle = ICompPriceOracle(_oldOracle);
    }

    function getUnderlyingPrice(address cToken)
        external
        view
        returns (uint256)
    {
        if (prices[cToken] == 0) {
            return oldOracle.getUnderlyingPrice(cToken);
        }
        return prices[cToken];
    }

    function setUnderlyingPrice(address cToken, uint256 price) external {
        prices[cToken] = price;
    }
}
