"""
Security Manager for Social Suit Application

This script provides comprehensive security management capabilities including:
- Running security audits
- Managing rate limiting
- Validating configurations
- Generating security reports
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import security modules
from services.security.security_audit import SecurityAuditor, run_security_audit
from services.security.rate_limiter import RateLimitConfig, RateLimiter
from services.database.redis import RedisManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    """Main security management class."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.logger = logger
        
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run a comprehensive security audit."""
        self.logger.info("Starting comprehensive security audit...")
        
        try:
            # Run security audit
            report = run_security_audit(str(self.project_root))
            
            # Save report to file
            report_file = self.project_root / f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Security audit completed. Report saved to {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error running security audit: {e}")
            raise

    async def check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting configuration and status."""
        self.logger.info("Checking rate limiting configuration...")
        
        try:
            # Initialize Redis connection
            await RedisManager.initialize()
            
            # Create rate limiter with default config
            config = RateLimitConfig()
            rate_limiter = RateLimiter(config)
            
            # Test rate limiting functionality
            test_results = await self._test_rate_limiting(rate_limiter)
            
            await RedisManager.close()
            
            return {
                "status": "operational",
                "config": {
                    "default_requests_per_minute": config.default_requests_per_minute,
                    "default_burst_size": config.default_burst_size,
                    "endpoint_limits": config.endpoint_limits,
                    "whitelist_ips": config.whitelist_ips,
                    "whitelist_paths": config.whitelist_paths
                },
                "test_results": test_results
            }
            
        except Exception as e:
            self.logger.error(f"Error checking rate limiting: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _test_rate_limiting(self, rate_limiter: RateLimiter) -> Dict[str, Any]:
        """Test rate limiting functionality."""
        test_results = {}
        
        try:
            # Test basic rate limiting
            test_ip = "192.168.1.100"
            test_path = "/api/v1/test"
            
            # Make several requests to test rate limiting
            allowed_requests = 0
            blocked_requests = 0
            
            for i in range(10):
                is_allowed = await rate_limiter.is_allowed(test_ip, test_path)
                if is_allowed:
                    allowed_requests += 1
                else:
                    blocked_requests += 1
            
            test_results["basic_test"] = {
                "allowed_requests": allowed_requests,
                "blocked_requests": blocked_requests,
                "test_ip": test_ip,
                "test_path": test_path
            }
            
            # Test whitelist functionality
            whitelist_ip = "127.0.0.1"
            whitelist_allowed = 0
            
            for i in range(5):
                is_allowed = await rate_limiter.is_allowed(whitelist_ip, test_path)
                if is_allowed:
                    whitelist_allowed += 1
            
            test_results["whitelist_test"] = {
                "whitelist_ip": whitelist_ip,
                "allowed_requests": whitelist_allowed,
                "expected": 5
            }
            
        except Exception as e:
            test_results["error"] = str(e)
        
        return test_results

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate security configuration files."""
        self.logger.info("Validating security configuration...")
        
        validation_results = {
            "config_files": {},
            "environment_variables": {},
            "recommendations": []
        }
        
        # Check configuration files
        config_files = [
            "core/config.py",
            ".env.example",
            "main.py"
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                validation_results["config_files"][config_file] = self._validate_config_file(file_path)
            else:
                validation_results["config_files"][config_file] = {
                    "exists": False,
                    "status": "missing"
                }
        
        # Check environment variables
        env_vars = [
            "JWT_SECRET",
            "DATABASE_URL",
            "REDIS_URL",
            "MONGODB_URL"
        ]
        
        for env_var in env_vars:
            validation_results["environment_variables"][env_var] = self._check_env_var(env_var)
        
        # Generate recommendations
        validation_results["recommendations"] = self._generate_config_recommendations(validation_results)
        
        return validation_results

    def _validate_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a specific configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                "exists": True,
                "size": len(content),
                "issues": []
            }
            
            # Check for common security issues
            if "DEBUG = True" in content:
                result["issues"].append("Debug mode enabled")
            
            if "SECRET_KEY = " in content and "os.environ" not in content:
                result["issues"].append("Hardcoded secret key detected")
            
            if "password" in content.lower() and "os.environ" not in content:
                result["issues"].append("Potential hardcoded password")
            
            result["status"] = "secure" if not result["issues"] else "issues_found"
            
            return result
            
        except Exception as e:
            return {
                "exists": True,
                "status": "error",
                "error": str(e)
            }

    def _check_env_var(self, var_name: str) -> Dict[str, Any]:
        """Check if environment variable is properly configured."""
        import os
        
        value = os.getenv(var_name)
        
        if value is None:
            return {
                "configured": False,
                "status": "missing",
                "recommendation": f"Set {var_name} environment variable"
            }
        
        # Basic validation
        if len(value) < 10:
            return {
                "configured": True,
                "status": "weak",
                "recommendation": f"{var_name} appears to be too short"
            }
        
        return {
            "configured": True,
            "status": "ok",
            "length": len(value)
        }

    def _generate_config_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate configuration recommendations based on validation results."""
        recommendations = []
        
        # Check config files
        for file_name, file_result in validation_results["config_files"].items():
            if not file_result.get("exists", False):
                recommendations.append(f"Create missing configuration file: {file_name}")
            elif file_result.get("issues"):
                for issue in file_result["issues"]:
                    recommendations.append(f"Fix {file_name}: {issue}")
        
        # Check environment variables
        for var_name, var_result in validation_results["environment_variables"].items():
            if not var_result.get("configured", False):
                recommendations.append(f"Configure environment variable: {var_name}")
            elif var_result.get("status") == "weak":
                recommendations.append(f"Strengthen {var_name}: {var_result.get('recommendation', '')}")
        
        return recommendations

    def generate_security_report(self, audit_report: Dict[str, Any], 
                                rate_limit_status: Dict[str, Any],
                                config_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive security report."""
        
        # Calculate overall security score
        audit_score = audit_report.get("security_score", 0)
        rate_limit_score = 100 if rate_limit_status.get("status") == "operational" else 50
        config_score = self._calculate_config_score(config_validation)
        
        overall_score = (audit_score + rate_limit_score + config_score) / 3
        
        # Determine security level
        if overall_score >= 90:
            security_level = "Excellent"
        elif overall_score >= 75:
            security_level = "Good"
        elif overall_score >= 60:
            security_level = "Fair"
        else:
            security_level = "Poor"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_security_score": round(overall_score, 2),
            "security_level": security_level,
            "component_scores": {
                "audit_score": audit_score,
                "rate_limit_score": rate_limit_score,
                "config_score": config_score
            },
            "audit_summary": {
                "total_findings": audit_report.get("total_findings", 0),
                "critical_findings": audit_report.get("findings_by_level", {}).get("critical", 0),
                "high_findings": audit_report.get("findings_by_level", {}).get("high", 0)
            },
            "rate_limiting": {
                "status": rate_limit_status.get("status", "unknown"),
                "test_results": rate_limit_status.get("test_results", {})
            },
            "configuration": {
                "issues_count": len([
                    issue for file_result in config_validation.get("config_files", {}).values()
                    for issue in file_result.get("issues", [])
                ]),
                "missing_env_vars": len([
                    var for var_result in config_validation.get("environment_variables", {}).values()
                    if not var_result.get("configured", False)
                ])
            },
            "recommendations": self._generate_overall_recommendations(
                audit_report, rate_limit_status, config_validation
            )
        }

    def _calculate_config_score(self, config_validation: Dict[str, Any]) -> float:
        """Calculate configuration security score."""
        total_files = len(config_validation.get("config_files", {}))
        total_env_vars = len(config_validation.get("environment_variables", {}))
        
        if total_files == 0 and total_env_vars == 0:
            return 0
        
        # Count issues
        file_issues = sum(
            len(file_result.get("issues", []))
            for file_result in config_validation.get("config_files", {}).values()
        )
        
        missing_env_vars = sum(
            1 for var_result in config_validation.get("environment_variables", {}).values()
            if not var_result.get("configured", False)
        )
        
        # Calculate score (100 - penalties)
        file_penalty = min(file_issues * 10, 50)  # Max 50 points penalty for file issues
        env_penalty = min(missing_env_vars * 15, 50)  # Max 50 points penalty for missing env vars
        
        return max(0, 100 - file_penalty - env_penalty)

    def _generate_overall_recommendations(self, audit_report: Dict[str, Any],
                                        rate_limit_status: Dict[str, Any],
                                        config_validation: Dict[str, Any]) -> List[str]:
        """Generate overall security recommendations."""
        recommendations = []
        
        # Add audit recommendations
        recommendations.extend(audit_report.get("recommendations", []))
        
        # Add rate limiting recommendations
        if rate_limit_status.get("status") != "operational":
            recommendations.append("Fix rate limiting configuration and ensure Redis connectivity")
        
        # Add configuration recommendations
        recommendations.extend(config_validation.get("recommendations", []))
        
        # Add general recommendations
        recommendations.extend([
            "Regularly update dependencies to patch security vulnerabilities",
            "Implement security monitoring and alerting",
            "Conduct regular security training for development team",
            "Set up automated security scanning in CI/CD pipeline"
        ])
        
        return list(set(recommendations))  # Remove duplicates

async def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description="Social Suit Security Manager")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--audit", action="store_true", help="Run security audit")
    parser.add_argument("--rate-limit-check", action="store_true", help="Check rate limiting")
    parser.add_argument("--config-validation", action="store_true", help="Validate configuration")
    parser.add_argument("--full-report", action="store_true", help="Generate full security report")
    parser.add_argument("--output", help="Output file for reports")
    
    args = parser.parse_args()
    
    security_manager = SecurityManager(args.project_root)
    
    try:
        if args.full_report or (not args.audit and not args.rate_limit_check and not args.config_validation):
            # Run full security assessment
            logger.info("Running full security assessment...")
            
            audit_report = await security_manager.run_full_audit()
            rate_limit_status = await security_manager.check_rate_limiting()
            config_validation = security_manager.validate_configuration()
            
            full_report = security_manager.generate_security_report(
                audit_report, rate_limit_status, config_validation
            )
            
            # Output results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(full_report, f, indent=2, default=str)
                logger.info(f"Full security report saved to {args.output}")
            else:
                print(json.dumps(full_report, indent=2, default=str))
        
        else:
            # Run individual checks
            if args.audit:
                audit_report = await security_manager.run_full_audit()
                print("Security Audit Results:")
                print(f"Security Score: {audit_report['security_score']}/100")
                print(f"Total Findings: {audit_report['total_findings']}")
                print(f"Critical: {audit_report['findings_by_level']['critical']}")
            
            if args.rate_limit_check:
                rate_limit_status = await security_manager.check_rate_limiting()
                print("Rate Limiting Status:")
                print(f"Status: {rate_limit_status['status']}")
                if 'test_results' in rate_limit_status:
                    print(f"Test Results: {rate_limit_status['test_results']}")
            
            if args.config_validation:
                config_validation = security_manager.validate_configuration()
                print("Configuration Validation:")
                print(f"Recommendations: {len(config_validation['recommendations'])}")
                for rec in config_validation['recommendations']:
                    print(f"  - {rec}")
    
    except Exception as e:
        logger.error(f"Error in security manager: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())