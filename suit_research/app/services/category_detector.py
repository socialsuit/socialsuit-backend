"""Category detection service for automatically categorizing projects."""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class CategoryKeywords:
    """Keywords associated with a specific category."""
    category: str
    keywords: List[str]
    weight: float = 1.0


class ProjectCategoryDetector:
    """Service for automatically detecting project categories based on various signals."""
    
    def __init__(self):
        self.category_keywords = self._initialize_category_keywords()
        self.domain_mappings = self._initialize_domain_mappings()
        self.token_mappings = self._initialize_token_mappings()
    
    def _initialize_category_keywords(self) -> List[CategoryKeywords]:
        """Initialize keyword mappings for each category."""
        return [
            # DeFi keywords
            CategoryKeywords(
                category="defi",
                keywords=[
                    "defi", "decentralized finance", "yield farming", "liquidity mining",
                    "automated market maker", "amm", "lending", "borrowing", "staking",
                    "yield", "swap", "liquidity pool", "farming", "vault", "protocol",
                    "synthetic", "derivatives", "options", "futures", "perpetual",
                    "flash loan", "collateral", "overcollateralized", "undercollateralized"
                ],
                weight=1.0
            ),
            
            # Layer 1 blockchains
            CategoryKeywords(
                category="layer_1",
                keywords=[
                    "blockchain", "layer 1", "l1", "consensus", "proof of stake", "pos",
                    "proof of work", "pow", "validator", "node", "mainnet", "genesis",
                    "smart contract platform", "virtual machine", "evm", "cosmos",
                    "substrate", "tendermint", "avalanche", "solana", "ethereum",
                    "bitcoin", "cardano", "polkadot", "algorand", "tezos", "near"
                ],
                weight=1.0
            ),
            
            # Layer 2 scaling solutions
            CategoryKeywords(
                category="layer_2",
                keywords=[
                    "layer 2", "l2", "scaling", "rollup", "optimistic rollup", "zk rollup",
                    "zero knowledge", "zk", "plasma", "state channel", "sidechain",
                    "polygon", "arbitrum", "optimism", "loopring", "immutable x",
                    "starknet", "zkSync", "hermez", "matic", "xdai", "gnosis chain"
                ],
                weight=1.0
            ),
            
            # NFT and digital collectibles
            CategoryKeywords(
                category="nft",
                keywords=[
                    "nft", "non-fungible token", "collectible", "digital art", "marketplace",
                    "opensea", "rarible", "foundation", "superrare", "async art",
                    "erc-721", "erc-1155", "metadata", "ipfs", "pfp", "avatar",
                    "generative art", "utility nft", "gaming nft", "metaverse nft"
                ],
                weight=1.0
            ),
            
            # Gaming and metaverse
            CategoryKeywords(
                category="gaming",
                keywords=[
                    "gaming", "game", "metaverse", "virtual world", "play to earn", "p2e",
                    "gamefi", "virtual reality", "vr", "augmented reality", "ar",
                    "sandbox", "decentraland", "axie infinity", "guild", "esports",
                    "in-game assets", "virtual land", "avatar", "mmorpg", "rpg"
                ],
                weight=1.0
            ),
            
            # Infrastructure and developer tools
            CategoryKeywords(
                category="infrastructure",
                keywords=[
                    "infrastructure", "node", "rpc", "api", "indexing", "graph",
                    "oracle", "chainlink", "band protocol", "tellor", "api3",
                    "cloud", "hosting", "cdn", "ipfs", "filecoin", "arweave",
                    "storage", "compute", "bandwidth", "networking", "middleware"
                ],
                weight=1.0
            ),
            
            # AI and machine learning
            CategoryKeywords(
                category="ai",
                keywords=[
                    "artificial intelligence", "ai", "machine learning", "ml",
                    "neural network", "deep learning", "natural language processing", "nlp",
                    "computer vision", "federated learning", "model training",
                    "data marketplace", "algorithm", "prediction", "automation"
                ],
                weight=1.0
            ),
            
            # Decentralized exchanges
            CategoryKeywords(
                category="dex",
                keywords=[
                    "dex", "decentralized exchange", "uniswap", "sushiswap", "pancakeswap",
                    "balancer", "curve", "1inch", "kyber", "bancor", "trading",
                    "order book", "market maker", "slippage", "arbitrage"
                ],
                weight=1.0
            ),
            
            # Wallets and custody
            CategoryKeywords(
                category="wallet",
                keywords=[
                    "wallet", "custody", "multisig", "hardware wallet", "cold storage",
                    "metamask", "trust wallet", "coinbase wallet", "ledger", "trezor",
                    "gnosis safe", "argent", "rainbow", "phantom", "solflare",
                    "private key", "seed phrase", "mnemonic", "keystore"
                ],
                weight=1.0
            ),
            
            # Developer tooling
            CategoryKeywords(
                category="tooling",
                keywords=[
                    "developer tools", "sdk", "api", "framework", "library",
                    "hardhat", "truffle", "remix", "brownie", "foundry",
                    "testing", "deployment", "monitoring", "analytics", "debugger",
                    "compiler", "linter", "formatter", "documentation", "tutorial"
                ],
                weight=1.0
            )
        ]
    
    def _initialize_domain_mappings(self) -> Dict[str, str]:
        """Initialize domain-to-category mappings for known projects."""
        return {
            # DeFi
            "uniswap.org": "dex",
            "sushiswap.fi": "dex",
            "pancakeswap.finance": "dex",
            "compound.finance": "defi",
            "aave.com": "defi",
            "makerdao.com": "defi",
            "yearn.finance": "defi",
            "curve.fi": "dex",
            "balancer.fi": "dex",
            
            # Layer 1
            "ethereum.org": "layer_1",
            "bitcoin.org": "layer_1",
            "solana.com": "layer_1",
            "cardano.org": "layer_1",
            "polkadot.network": "layer_1",
            "avalanche.org": "layer_1",
            "algorand.org": "layer_1",
            "near.org": "layer_1",
            
            # Layer 2
            "polygon.technology": "layer_2",
            "arbitrum.io": "layer_2",
            "optimism.io": "layer_2",
            "loopring.org": "layer_2",
            "immutable.com": "layer_2",
            "starknet.io": "layer_2",
            "zksync.io": "layer_2",
            
            # NFT
            "opensea.io": "nft",
            "rarible.com": "nft",
            "foundation.app": "nft",
            "superrare.com": "nft",
            "async.art": "nft",
            
            # Gaming
            "sandbox.game": "gaming",
            "decentraland.org": "gaming",
            "axieinfinity.com": "gaming",
            "illuvium.io": "gaming",
            "gala.games": "gaming",
            
            # Infrastructure
            "chainlink.com": "infrastructure",
            "thegraph.com": "infrastructure",
            "filecoin.io": "infrastructure",
            "arweave.org": "infrastructure",
            "livepeer.org": "infrastructure",
            
            # Wallets
            "metamask.io": "wallet",
            "trustwallet.com": "wallet",
            "argent.xyz": "wallet",
            "rainbow.me": "wallet",
            "phantom.app": "wallet"
        }
    
    def _initialize_token_mappings(self) -> Dict[str, str]:
        """Initialize token symbol to category mappings."""
        return {
            # DeFi tokens
            "UNI": "dex",
            "SUSHI": "dex",
            "CAKE": "dex",
            "COMP": "defi",
            "AAVE": "defi",
            "MKR": "defi",
            "YFI": "defi",
            "CRV": "dex",
            "BAL": "dex",
            "SNX": "defi",
            
            # Layer 1 tokens
            "ETH": "layer_1",
            "BTC": "layer_1",
            "SOL": "layer_1",
            "ADA": "layer_1",
            "DOT": "layer_1",
            "AVAX": "layer_1",
            "ALGO": "layer_1",
            "NEAR": "layer_1",
            
            # Layer 2 tokens
            "MATIC": "layer_2",
            "ARB": "layer_2",
            "OP": "layer_2",
            "LRC": "layer_2",
            "IMX": "layer_2",
            
            # Infrastructure tokens
            "LINK": "infrastructure",
            "GRT": "infrastructure",
            "FIL": "infrastructure",
            "AR": "infrastructure",
            "LPT": "infrastructure",
            
            # Gaming tokens
            "SAND": "gaming",
            "MANA": "gaming",
            "AXS": "gaming",
            "ILV": "gaming",
            "GALA": "gaming"
        }
    
    def detect_category(self, 
                       name: str = None, 
                       description: str = None, 
                       website: str = None, 
                       token_symbol: str = None) -> Optional[str]:
        """Detect project category based on available information."""
        
        # Check token symbol mapping first (highest confidence)
        if token_symbol and token_symbol.upper() in self.token_mappings:
            return self.token_mappings[token_symbol.upper()]
        
        # Check domain mapping
        if website:
            domain = self._extract_domain(website)
            if domain in self.domain_mappings:
                return self.domain_mappings[domain]
        
        # Analyze text content for keywords
        text_content = ""
        if name:
            text_content += f" {name}"
        if description:
            text_content += f" {description}"
        if website:
            text_content += f" {website}"
        
        if text_content.strip():
            return self._analyze_text_content(text_content.lower())
        
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove www prefix
        url = re.sub(r'^www\.', '', url)
        # Extract domain (everything before first slash)
        domain = url.split('/')[0]
        return domain.lower()
    
    def _analyze_text_content(self, text: str) -> Optional[str]:
        """Analyze text content to determine category based on keywords."""
        category_scores = {}
        
        for category_keywords in self.category_keywords:
            score = 0
            for keyword in category_keywords.keywords:
                # Count keyword occurrences (case insensitive)
                count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
                score += count * category_keywords.weight
            
            if score > 0:
                category_scores[category_keywords.category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def get_category_confidence(self, 
                               category: str,
                               name: str = None, 
                               description: str = None, 
                               website: str = None, 
                               token_symbol: str = None) -> float:
        """Get confidence score for a detected category (0.0 to 1.0)."""
        
        # High confidence for exact token/domain matches
        if token_symbol and token_symbol.upper() in self.token_mappings:
            if self.token_mappings[token_symbol.upper()] == category:
                return 0.95
        
        if website:
            domain = self._extract_domain(website)
            if domain in self.domain_mappings:
                if self.domain_mappings[domain] == category:
                    return 0.90
        
        # Medium confidence for keyword matches
        text_content = ""
        if name:
            text_content += f" {name}"
        if description:
            text_content += f" {description}"
        if website:
            text_content += f" {website}"
        
        if text_content.strip():
            detected_category = self._analyze_text_content(text_content.lower())
            if detected_category == category:
                # Calculate confidence based on keyword density
                total_words = len(text_content.split())
                if total_words > 0:
                    return min(0.8, 0.3 + (0.5 * min(5, total_words) / total_words))
        
        return 0.0


# Global instance
category_detector = ProjectCategoryDetector()