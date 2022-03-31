// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;

import {SafeMath} from "@openzeppelin/contracts/math/SafeMath.sol";
import "./interfaces/comppriceoracle.sol";
import "./interfaces/comptroller.sol";
import "./interfaces/ipriceoracle.sol";

contract ScreamPriceOracle is IPriceOracle {
    using SafeMath for uint256;

    address cTokenQuote;
    address cTokenBase;
    ComptrollerV5Storage comptroller;

    constructor(
        address _comptroller,
        address _cTokenQuote,
        address _cTokenBase
    ) public {
        cTokenQuote = _cTokenQuote;
        cTokenBase = _cTokenBase;
        comptroller = ComptrollerV5Storage(_comptroller);
    }

    function getPrice() external view override returns (uint256) {
        ICompPriceOracle oracle = ICompPriceOracle(comptroller.oracle());

        // If price returns 0, the price is not available
        uint256 quotePrice = oracle.getUnderlyingPrice(cTokenQuote);
        require(quotePrice != 0);

        uint256 basePrice = oracle.getUnderlyingPrice(cTokenBase);
        require(basePrice != 0);

        return basePrice.mul(1e18).div(quotePrice);
    }
}
