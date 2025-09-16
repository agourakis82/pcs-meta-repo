"""
Configuration for Advanced Rate Limiting System
Centralized configuration management for rate limiting rules and settings
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .advanced_limiter import RateLimitRule, RateLimitScope, RateLimitStrategy

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    redis_url: str = "redis://localhost:6379"
    key_prefix: str = "pcs_h3_rate_limit"
    metrics_enabled: bool = True
    default_rules_enabled: bool = True
    custom_rules: Dict[str, dict] = None
    exclude_paths: List[str] = None
    header_prefix: str = "X-RateLimit"
    
    def __post_init__(self):
        if self.custom_rules is None:
            self.custom_rules = {}
        if self.exclude_paths is None:
            self.exclude_paths = ["/health", "/docs", "/redoc", "/openapi.json"]


class RateLimitConfigManager:
    """Manages rate limiting configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = RateLimitConfig()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if not self.config_path:
            return
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    data = json.load(f)
                else:
                    logger.error(f"Unsupported config format: {config_file.suffix}")
                    return
            
            # Update config with loaded data
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            logger.info(f"Rate limiting config loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self, path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = path or self.config_path
        if not save_path:
            logger.error("No config path specified")
            return False
        
        try:
            config_file = Path(save_path)
            config_data = {
                'redis_url': self.config.redis_url,
                'key_prefix': self.config.key_prefix,
                'metrics_enabled': self.config.metrics_enabled,
                'default_rules_enabled': self.config.default_rules_enabled,
                'custom_rules': self.config.custom_rules,
                'exclude_paths': self.config.exclude_paths,
                'header_prefix': self.config.header_prefix
            }
            
            with open(config_file, 'w') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False)
                elif config_file.suffix == '.json':
                    json.dump(config_data, f, indent=2)
            
            logger.info(f"Rate limiting config saved to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_rule_configs(self) -> Dict[str, RateLimitRule]:
        """Convert config to RateLimitRule objects"""
        rules = {}
        
        # Add default rules if enabled
        if self.config.default_rules_enabled:
            rules.update(self._get_default_rules())
        
        # Add custom rules
        for name, rule_config in self.config.custom_rules.items():
            try:
                rule = RateLimitRule(
                    scope=RateLimitScope(rule_config["scope"]),
                    strategy=RateLimitStrategy(rule_config["strategy"]),
                    limit=rule_config["limit"],
                    window=rule_config["window"],
                    burst=rule_config.get("burst"),
                    leak_rate=rule_config.get("leak_rate"),
                    enabled=rule_config.get("enabled", True),
                    priority=rule_config.get("priority", 0)
                )
                rules[name] = rule
            except Exception as e:
                logger.error(f"Error creating rule {name}: {e}")
        
        return rules
    
    def _get_default_rules(self) -> Dict[str, RateLimitRule]:
        """Get default rate limiting rules"""
        return {
            "global_burst": RateLimitRule(
                scope=RateLimitScope.GLOBAL,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=10000,
                window=60,
                priority=10
            ),
            "ip_moderate": RateLimitRule(
                scope=RateLimitScope.IP,
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                limit=1000,
                window=60,
                priority=20
            ),
            "user_standard": RateLimitRule(
                scope=RateLimitScope.USER,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                limit=500,
                window=60,
                burst=100,
                priority=30
            ),
            "endpoint_protection": RateLimitRule(
                scope=RateLimitScope.ENDPOINT,
                strategy=RateLimitStrategy.FIXED_WINDOW,
                limit=100,
                window=60,
                priority=25
            ),
            "user_endpoint_strict": RateLimitRule(
                scope=RateLimitScope.USER_ENDPOINT,
                strategy=RateLimitStrategy.LEAKY_BUCKET,
                limit=50,
                window=60,
                leak_rate=1.0,
                priority=40
            )
        }
    
    def add_custom_rule(self, name: str, rule_config: dict):
        """Add a custom rule configuration"""
        self.config.custom_rules[name] = rule_config
        logger.info(f"Added custom rule: {name}")
    
    def remove_custom_rule(self, name: str):
        """Remove a custom rule configuration"""
        if name in self.config.custom_rules:
            del self.config.custom_rules[name]
            logger.info(f"Removed custom rule: {name}")
    
    def update_rule(self, name: str, **kwargs):
        """Update an existing rule configuration"""
        if name in self.config.custom_rules:
            self.config.custom_rules[name].update(kwargs)
            logger.info(f"Updated rule: {name}")
        else:
            logger.warning(f"Rule not found: {name}")


# Predefined configuration templates
RATE_LIMIT_TEMPLATES = {
    "strict": {
        "redis_url": "redis://localhost:6379",
        "key_prefix": "pcs_h3_rate_limit_strict",
        "metrics_enabled": True,
        "default_rules_enabled": False,
        "custom_rules": {
            "global_strict": {
                "scope": "global",
                "strategy": "sliding_window",
                "limit": 5000,
                "window": 60,
                "priority": 10
            },
            "ip_strict": {
                "scope": "ip",
                "strategy": "sliding_window",
                "limit": 100,
                "window": 60,
                "priority": 20
            },
            "user_strict": {
                "scope": "user",
                "strategy": "token_bucket",
                "limit": 50,
                "window": 60,
                "burst": 10,
                "priority": 30
            }
        },
        "exclude_paths": ["/health"],
        "header_prefix": "X-RateLimit"
    },
    
    "moderate": {
        "redis_url": "redis://localhost:6379",
        "key_prefix": "pcs_h3_rate_limit_moderate",
        "metrics_enabled": True,
        "default_rules_enabled": True,
        "custom_rules": {
            "api_protection": {
                "scope": "endpoint",
                "strategy": "sliding_window",
                "limit": 200,
                "window": 60,
                "priority": 25
            }
        },
        "exclude_paths": ["/health", "/docs", "/redoc", "/openapi.json"],
        "header_prefix": "X-RateLimit"
    },
    
    "lenient": {
        "redis_url": "redis://localhost:6379",
        "key_prefix": "pcs_h3_rate_limit_lenient",
        "metrics_enabled": True,
        "default_rules_enabled": False,
        "custom_rules": {
            "global_lenient": {
                "scope": "global",
                "strategy": "fixed_window",
                "limit": 50000,
                "window": 60,
                "priority": 10
            },
            "ip_lenient": {
                "scope": "ip",
                "strategy": "token_bucket",
                "limit": 5000,
                "window": 60,
                "burst": 1000,
                "priority": 20
            }
        },
        "exclude_paths": ["/health", "/docs", "/redoc", "/openapi.json", "/static"],
        "header_prefix": "X-RateLimit"
    }
}


def create_config_from_template(template_name: str) -> RateLimitConfigManager:
    """Create configuration from predefined template"""
    if template_name not in RATE_LIMIT_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    config_manager = RateLimitConfigManager()
    template_data = RATE_LIMIT_TEMPLATES[template_name]
    
    for key, value in template_data.items():
        if hasattr(config_manager.config, key):
            setattr(config_manager.config, key, value)
    
    logger.info(f"Created rate limiting config from template: {template_name}")
    return config_manager


def load_config_from_env() -> RateLimitConfigManager:
    """Load configuration from environment variables"""
    import os
    
    config_manager = RateLimitConfigManager()
    
    # Override with environment variables
    if os.getenv("RATE_LIMIT_REDIS_URL"):
        config_manager.config.redis_url = os.getenv("RATE_LIMIT_REDIS_URL")
    
    if os.getenv("RATE_LIMIT_KEY_PREFIX"):
        config_manager.config.key_prefix = os.getenv("RATE_LIMIT_KEY_PREFIX")
    
    if os.getenv("RATE_LIMIT_METRICS_ENABLED"):
        config_manager.config.metrics_enabled = os.getenv("RATE_LIMIT_METRICS_ENABLED").lower() == "true"
    
    if os.getenv("RATE_LIMIT_DEFAULT_RULES_ENABLED"):
        config_manager.config.default_rules_enabled = os.getenv("RATE_LIMIT_DEFAULT_RULES_ENABLED").lower() == "true"
    
    logger.info("Rate limiting config loaded from environment")
    return config_manager


# Example configuration files
EXAMPLE_YAML_CONFIG = """
redis_url: "redis://localhost:6379"
key_prefix: "pcs_h3_rate_limit"
metrics_enabled: true
default_rules_enabled: true
custom_rules:
  admin_bypass:
    scope: "user"
    strategy: "token_bucket"
    limit: 10000
    window: 60
    burst: 1000
    priority: 50
    enabled: true
  sensitive_endpoint:
    scope: "endpoint"
    strategy: "leaky_bucket"
    limit: 10
    window: 60
    leak_rate: 0.5
    priority: 60
    enabled: true
exclude_paths:
  - "/health"
  - "/docs"
  - "/redoc"
  - "/openapi.json"
header_prefix: "X-RateLimit"
"""

EXAMPLE_JSON_CONFIG = """
{
  "redis_url": "redis://localhost:6379",
  "key_prefix": "pcs_h3_rate_limit",
  "metrics_enabled": true,
  "default_rules_enabled": true,
  "custom_rules": {
    "admin_bypass": {
      "scope": "user",
      "strategy": "token_bucket",
      "limit": 10000,
      "window": 60,
      "burst": 1000,
      "priority": 50,
      "enabled": true
    }
  },
  "exclude_paths": ["/health", "/docs", "/redoc", "/openapi.json"],
  "header_prefix": "X-RateLimit"
}
"""


def save_example_configs(directory: str = "."):
    """Save example configuration files"""
    try:
        yaml_path = Path(directory) / "rate_limit_config.yaml"
        json_path = Path(directory) / "rate_limit_config.json"
        
        with open(yaml_path, 'w') as f:
            f.write(EXAMPLE_YAML_CONFIG)
        
        with open(json_path, 'w') as f:
            f.write(EXAMPLE_JSON_CONFIG)
        
        logger.info(f"Example configs saved to {directory}")
        return True
    except Exception as e:
        logger.error(f"Error saving example configs: {e}")
        return False