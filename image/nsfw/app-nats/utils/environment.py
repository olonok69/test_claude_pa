import os
import platform
import socket
import subprocess


def detect_environment():
    # Initialize with unknown environment
    environment = "Unknown"

    # Get basic system info
    system = platform.system()

    # 1) Check if running on Windows (local)
    if system == "Windows":
        # Check if not in any container or CI/CD
        if not is_in_container() and not is_in_cicd():
            return "Local Windows"

    # 2) Check if running in WSL
    elif system == "Linux":
        environment = "Linux Host"
        # WSL-specific checks
        if os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()
                if "microsoft" in version_info or "wsl" in version_info:
                    return "Windows Subsystem for Linux (WSL)"

        # 3) Check if in Docker container
        elif is_in_docker():
            # Additional check for Docker Desktop (local)
            environment = "Docker Container"
            if is_docker_desktop():
                return "Docker Container on Docker Desktop"
            # 6) Check if in Kubernetes (AKS or other K8s)
            elif is_in_kubernetes():
                return "Kubernetes Pod"
            return environment

        # 5) Check if this is a regular Linux VM
        elif is_linux_vm():
            return "Linux Virtual Machine"

    # 4) Check if in CI/CD pipeline
    if is_in_cicd() and environment == "Unknown":

        return "CI/CD Pipeline"
    return environment


def is_in_container():
    """Check if running inside a container (Docker or other)"""
    # Check for container environment indicators
    if os.path.exists("/.dockerenv"):
        return True

    # Check if running in cgroup
    if os.path.exists("/proc/1/cgroup"):
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read() or "kubepods" in f.read()

    return False


def is_in_docker():
    """Specific check for Docker containers"""
    if os.path.exists("/.dockerenv"):
        return True

    if os.path.exists("/proc/1/cgroup"):
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read()

    return False


def is_docker_desktop():
    """Try to determine if this is Docker Desktop"""
    # This is a heuristic - Docker Desktop usually runs on Windows/Mac host
    try:
        # Check hostname patterns often used in Docker Desktop
        hostname = socket.gethostname()
        return (
            "docker-desktop" in hostname.lower() or "desktop-docker" in hostname.lower()
        )
    except:
        return False


def is_in_kubernetes():
    """Check if running in Kubernetes"""
    # Check for Kubernetes-specific environment variables
    if "KUBERNETES_SERVICE_HOST" in os.environ:
        return True

    # Check cgroups for Kubernetes indicators
    if os.path.exists("/proc/1/cgroup"):
        with open("/proc/1/cgroup", "r") as f:
            return "kubepods" in f.read()

    return False


def is_linux_vm():
    """Check if running on a Linux VM without requiring sudo"""
    # Check if system is Linux
    if platform.system() != "Linux":
        return False

    # Not in container, not in WSL
    if is_in_container() or is_wsl():
        return False

    # Check for VM indicators that don't require sudo
    vm_indicators = False

    # Check for common VM-specific files or directories
    vm_files = [
        "/sys/class/dmi/id/product_name",
        "/sys/class/dmi/id/sys_vendor",
        "/proc/scsi/scsi",  # Often contains VM-specific storage controllers
    ]

    for file_path in vm_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read().lower()
                    if any(
                        indicator in content
                        for indicator in [
                            "vmware",
                            "virtualbox",
                            "kvm",
                            "xen",
                            "qemu",
                            "hyperv",
                            "virtual",
                            "amazon",
                            "ec2",
                            "azure",
                        ]
                    ):
                        vm_indicators = True
                        break
            except:
                pass

    # Check if DMI data is available (often accessible without sudo)
    try:
        # Try to get system manufacturer without sudo
        result = subprocess.run(["hostnamectl"], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.lower()
            if any(
                vm in output
                for vm in [
                    "vmware",
                    "virtualbox",
                    "kvm",
                    "xen",
                    "qemu",
                    "microsoft",
                    "amazon",
                    "google",
                    "virtual machine",
                    "azure",
                    "hyper-v",
                    "computer-vm",
                ]
            ):
                vm_indicators = True
    except:
        pass

    # Check /proc/cpuinfo for virtualization flags
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read().lower()
            if any(term in cpuinfo for term in ["hypervisor", "vmx", "svm"]):
                vm_indicators = True
    except:
        pass

    return vm_indicators


def is_wsl():
    """Specific check for WSL environment"""
    if os.path.exists("/proc/version"):
        with open("/proc/version", "r") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info or "wsl" in version_info
    return False


def is_in_cicd():
    """Check if running in CI/CD pipeline"""
    # Check for common CI/CD environment variables
    ci_env_vars = [
        # GitHub Actions
        "GITHUB_ACTIONS",
        "GITHUB_WORKFLOW",
        "GITHUB_RUN_ID",
        # Azure DevOps
        "TF_BUILD",
        "AGENT_NAME",
        "BUILD_BUILDID",
        # Other common CI systems
        "CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
    ]

    return any(env_var in os.environ for env_var in ci_env_vars)


# Example usage
if __name__ == "__main__":
    env = detect_environment()
    print(f"Running in environment: {env}")
