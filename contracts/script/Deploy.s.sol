// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/SignalWarsAgentRegistry.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        SignalWarsAgentRegistry registry = new SignalWarsAgentRegistry();
        
        console.log("SignalWarsAgentRegistry deployed at:", address(registry));
        
        vm.stopBroadcast();
    }
}
