from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import Optional
import yaml # For describe_kubernetes_resource
import base64 # For secret data encoding/decoding

# Load Kubernetes configuration.
# This will load the configuration from the default location (~/.kube/config)
# or from the in-cluster service account environment.
try:
    config.load_kube_config()
except config.ConfigException:
    try:
        config.load_incluster_config()
    except config.ConfigException as e:
        raise Exception("Could not configure kubernetes client") from e


v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
autoscaling_v1 = client.AutoscalingV1Api() # For HPA resources
networking_v1 = client.NetworkingV1Api() # For Ingress resources


def create_kubernetes_pod(name: str, image: str, namespace: str = "default", port: Optional[int] = None) -> str:
    """Create a Kubernetes Pod with the given name, image, namespace, and optional port."""
    try:
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": name},
            "spec": {
                "containers": [
                    {"name": name, "image": image}
                ]
            }
        }
        if port:
            pod_manifest["spec"]["containers"][0]["ports"] = [{"containerPort": port}]
        v1.create_namespaced_pod(body=pod_manifest, namespace=namespace)
        return f"Pod {name} created successfully in namespace {namespace}."
    except ApiException as e:
        return f"Error creating pod {name}: {e}"

def delete_kubernetes_pod(name: str, namespace: str = "default", confirm: bool = False) -> str:
    """Delete a Kubernetes Pod by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete pod '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete pod {name}'."
        v1.delete_namespaced_pod(name=name, namespace=namespace)
        return f"Pod {name} deleted successfully from namespace {namespace}."
    except ApiException as e:
        if e.status == 404:
            return f"Pod {name} not found in namespace {namespace}."
        return f"Error deleting pod {name}: {e}"

def create_kubernetes_namespace(name: str) -> str:
    """Create a Kubernetes Namespace with the given name."""
    try:
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": name}
        }
        v1.create_namespace(body=namespace_manifest)
        return f"Namespace {name} created successfully."
    except ApiException as e:
        return f"Error creating namespace {name}: {e}"

def delete_kubernetes_namespace(name: str, confirm: bool = False) -> str:
    """Delete a Kubernetes Namespace by name."""
    try:
        if not confirm:
            return f"Confirmation required to delete namespace '{name}'. Please confirm by saying 'yes, delete namespace {name}'."
        v1.delete_namespace(name=name)
        return f"Namespace {name} deleted successfully."
    except ApiException as e:
        if e.status == 404:
            return f"Namespace {name} not found."
        return f"Error deleting namespace {name}: {e}"

def create_kubernetes_deployment(name: str, image: str, replicas: int = 1, namespace: str = "default", port: Optional[int] = None) -> str:
    """Create a Kubernetes Deployment with the given name, image, replicas, namespace, and optional port."""
    try:
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": name}},
                "template": {
                    "metadata": {"labels": {"app": name}},
                    "spec": {
                        "containers": [
                            {"name": name, "image": image}
                        ]
                    }
                }
            }
        }
        if port:
            deployment_manifest["spec"]["template"]["spec"]["containers"][0]["ports"] = [{"containerPort": port}]
        apps_v1.create_namespaced_deployment(body=deployment_manifest, namespace=namespace)
        return f"Deployment {name} created successfully in namespace {namespace}."
    except ApiException as e:
        return f"Error creating deployment {name}: {e}"

def delete_kubernetes_deployment(name: str, namespace: str = "default", confirm: bool = False) -> str:
    """Delete a Kubernetes Deployment by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete deployment '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete deployment {name}'."
        apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
        return f"Deployment {name} deleted successfully from namespace {namespace}."
    except ApiException as e:
        if e.status == 404:
            return f"Deployment {name} not found in namespace {namespace}."
        return f"Error deleting deployment {name}: {e}"

def create_kubernetes_service(name: str, selector_app: str, port: int, target_port: int, namespace: str = "default", service_type: str = "ClusterIP") -> str:
    """Create a Kubernetes Service with the given name, selector, port, target port, namespace, and optional type."""
    try:
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": name},
            "spec": {
                "selector": {"app": selector_app},
                "ports": [{"protocol": "TCP", "port": port, "targetPort": target_port}],
                "type": service_type
            }
        }
        v1.create_namespaced_service(body=service_manifest, namespace=namespace)
        return f"Service {name} created successfully in namespace {namespace}."
    except ApiException as e:
        return f"Error creating service {name}: {e}"

def delete_kubernetes_service(name: str, namespace: str = "default", confirm: bool = False) -> str:
    """Delete a Kubernetes Service by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete service '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete service {name}'."
        v1.delete_namespaced_service(name=name, namespace=namespace)
        return f"Service {name} deleted successfully from namespace {namespace}."
    except ApiException as e:
        if e.status == 404:
            return f"Service {name} not found in namespace {namespace}."
        return f"Error deleting service {name}: {e}"

def list_kubernetes_services(namespace: Optional[str] = None) -> str:
    """List all Kubernetes services in a given namespace or all namespaces if none is specified."""
    try:
        if namespace:
            services = [svc.metadata.name for svc in v1.list_namespaced_service(namespace=namespace).items]
            return f"Services in namespace {namespace}: {', '.join(services)}"
        else:
            services = [svc.metadata.name for svc in v1.list_service_for_all_namespaces().items]
            return f"All services: {', '.join(services)}"
    except ApiException as e:
        return f"Error listing services: {e}"

def list_kubernetes_deployments(namespace: Optional[str] = None) -> str:
    """List all Kubernetes deployments in a given namespace or all namespaces if none is specified."""
    try:
        if namespace:
            deployments = [dep.metadata.name for dep in apps_v1.list_namespaced_deployment(namespace=namespace).items]
            return f"Deployments in namespace {namespace}: {', '.join(deployments)}"
        else:
            deployments = [dep.metadata.name for dep in apps_v1.list_deployment_for_all_namespaces().items]
            return f"All deployments: {', '.join(deployments)}"
    except ApiException as e:
        return f"Error listing deployments: {e}"

def list_kubernetes_namespaces() -> str:
    """List all Kubernetes namespaces."""
    try:
        namespaces = [ns.metadata.name for ns in v1.list_namespace().items]
        return f"Available namespaces: {', '.join(namespaces)}"
    except ApiException as e:
        return f"Error listing namespaces: {e}"

def get_kubernetes_pod(name: str, namespace: str = "default") -> str:
    """Get details of a specific Kubernetes pod by name and namespace."""
    try:
        pod = v1.read_namespaced_pod(name=name, namespace=namespace)
        return f"Pod {name} in namespace {namespace}: Status={pod.status.phase}, IP={pod.status.pod_ip}"
    except ApiException as e:
        if e.status == 404:
            return f"Pod {name} not found in namespace {namespace}."
        return f"Error getting pod {name}: {e}"

def list_kubernetes_pods(namespace: Optional[str] = None) -> str:
    """List all Kubernetes pods in a given namespace or all namespaces if none is specified."""
    try:
        if namespace:
            pods = [pod.metadata.name for pod in v1.list_namespaced_pod(namespace=namespace).items]
            return f"Pods in namespace {namespace}: {', '.join(pods)}"
        else:
            pods = [pod.metadata.name for pod in v1.list_pod_for_all_namespaces().items]
            return f"All pods: {', '.join(pods)}"
    except ApiException as e:
        return f"Error listing pods: {e}"

def scale_kubernetes_deployment(name: str, replicas: int, namespace: str = "default") -> str:
    """Scale a Kubernetes Deployment to a specific number of replicas."""
    try:
        # Ensure replicas is a non-negative integer
        if not isinstance(replicas, int) or replicas < 0:
            return "Error: Replicas must be a non-negative integer."

        # Create a patch to update the number of replicas
        patch = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=patch)
        return f"Deployment {name} in namespace {namespace} scaled to {replicas} replicas successfully."
    except ApiException as e:
        if e.status == 404:
            return f"Deployment {name} not found in namespace {namespace}."
        return f"Error scaling deployment {name}: {e}"

def get_kubernetes_deployment_status(name: str, namespace: str = "default") -> str:
    """Get the status of a Kubernetes Deployment, including replica counts and conditions."""
    try:
        deployment = apps_v1.read_namespaced_deployment_status(name=name, namespace=namespace)
        status = deployment.status
        
        available_replicas = status.available_replicas or 0
        ready_replicas = status.ready_replicas or 0
        total_replicas = status.replicas or 0
        updated_replicas = status.updated_replicas or 0
        
        conditions_str = "No conditions reported."
        if status.conditions:
            conditions_list = []
            for c in status.conditions:
                conditions_list.append(f"- {c.type}: {c.status} (Reason: {c.reason}, Message: {c.message})")
            conditions_str = "\n".join(conditions_list)

        return (
            f"Deployment '{name}' in namespace '{namespace}' Status:\n"
            f"  Replicas: {ready_replicas} ready / {available_replicas} available / {updated_replicas} updated / {total_replicas} total\n"
            f"Conditions:\n{conditions_str}"
        )
    except ApiException as e:
        if e.status == 404:
            return f"Deployment {name} not found in namespace {namespace}."
        return f"Error getting deployment status for {name}: {e}"

def get_kubernetes_config_map(name: str, namespace: str = "default") -> str:
    """Get the details and data of a specific Kubernetes ConfigMap."""
    try:
        config_map = v1.read_namespaced_config_map(name=name, namespace=namespace)
        data_str = "No data."
        if config_map.data:
            data_items = [f"  {key}: {value}" for key, value in config_map.data.items()]
            data_str = "\n".join(data_items)
        return f"ConfigMap '{name}' in namespace '{namespace}':\nData:\n{data_str}"
    except ApiException as e:
        if e.status == 404:
            return f"ConfigMap '{name}' not found in namespace '{namespace}'."
        return f"Error getting ConfigMap '{name}': {e}"

def create_kubernetes_secret(name: str, namespace: str, data: dict, secret_type: str = "Opaque") -> str:
    """Create a Kubernetes Secret with the given name, namespace, data (dict), and type."""
    try:
        # Base64 encode all data values
        encoded_data = {k: base64.b64encode(v.encode('utf-8')).decode('utf-8') for k, v in data.items()}

        secret_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": name},
            "type": secret_type,
            "data": encoded_data
        }
        v1.create_namespaced_secret(body=secret_manifest, namespace=namespace)
        return f"Secret '{name}' created successfully in namespace '{namespace}'."
    except ApiException as e:
        return f"Error creating Secret '{name}': {e}"

def delete_kubernetes_secret(name: str, namespace: str, confirm: bool = False) -> str:
    """Delete a Kubernetes Secret by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete Secret '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete secret {name}'."
        v1.delete_namespaced_secret(name=name, namespace=namespace)
        return f"Secret '{name}' deleted successfully from namespace '{namespace}'."
    except ApiException as e:
        if e.status == 404:
            return f"Secret '{name}' not found in namespace '{namespace}'."
        return f"Error deleting Secret '{name}': {e}"

def get_kubernetes_secret(name: str, namespace: str, mask_data: bool = True) -> str:
    """
    Get details and data of a specific Kubernetes Secret.
    Sensitive data will be masked by default.
    """
    try:
        secret = v1.read_namespaced_secret(name=name, namespace=namespace)
        data_str = "No data."
        if secret.data:
            data_items = []
            for key, value_b64 in secret.data.items():
                # Decoded value is only used if mask_data is False
                decoded_value = base64.b64decode(value_b64).decode('utf-8')
                if mask_data:
                    data_items.append(f"  {key}: {'********'}") # Mask sensitive data
                else:
                    data_items.append(f"  {key}: {decoded_value}")
            data_str = "\n".join(data_items)
        
        return (f"Secret '{name}' in namespace '{namespace}':\n"
                f"Type: {secret.type}\n"
                f"Data:\n{data_str}")
    except ApiException as e:
        if e.status == 404:
            return f"Secret '{name}' not found in namespace '{namespace}'."
        return f"Error getting Secret '{name}': {e}"

def create_kubernetes_ingress(name: str, namespace: str, host: str, service_name: str, service_port: int, path: str = "/") -> str:
    """Create a Kubernetes Ingress resource."""
    try:
        ingress_manifest = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": name},
            "spec": {
                "rules": [
                    {
                        "host": host,
                        "http": {
                            "paths": [
                                {
                                    "path": path,
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": service_name,
                                            "port": {"number": service_port}
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        networking_v1.create_namespaced_ingress(body=ingress_manifest, namespace=namespace)
        return f"Ingress '{name}' created successfully in namespace '{namespace}' for host '{host}'."
    except ApiException as e:
        return f"Error creating Ingress '{name}': {e}"

def delete_kubernetes_ingress(name: str, namespace: str, confirm: bool = False) -> str:
    """Delete a Kubernetes Ingress resource by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete Ingress '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete ingress {name}'."
        networking_v1.delete_namespaced_ingress(name=name, namespace=namespace)
        return f"Ingress '{name}' deleted successfully from namespace '{namespace}'."
    except ApiException as e:
        if e.status == 404:
            return f"Ingress '{name}' not found in namespace '{namespace}'."
        return f"Error deleting Ingress '{name}': {e}"

def get_kubernetes_ingress(name: str, namespace: str) -> str:
    """Get details of a specific Kubernetes Ingress resource."""
    try:
        ingress = networking_v1.read_namespaced_ingress(name=name, namespace=namespace)
        rules_str = "No rules defined."
        if ingress.spec.rules:
            rule_details = []
            for rule in ingress.spec.rules:
                host = rule.host or "N/A"
                paths = []
                if rule.http and rule.http.paths:
                    for p in rule.http.paths:
                        backend_svc = p.backend.service.name if p.backend and p.backend.service else "N/A"
                        backend_port = p.backend.service.port.number if p.backend and p.backend.service and p.backend.service.port else "N/A"
                        paths.append(f"  - Path: {p.path or '/'}, Type: {p.path_type or 'Prefix'}, Backend: {backend_svc}:{backend_port}")
                rule_details.append(f"  Host: {host}\n" + "\n".join(paths))
            rules_str = "\n".join(rule_details)
        return f"Ingress '{name}' in namespace '{namespace}':\nRules:\n{rules_str}"
    except ApiException as e:
        if e.status == 404:
            return f"Ingress '{name}' not found in namespace '{namespace}'."
        return f"Error getting Ingress '{name}': {e}"

def get_kubernetes_hpa_status(name: str, namespace: str = "default") -> str:
    """Get the status of a specific Horizontal Pod Autoscaler (HPA)."""
    try:
        hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler_status(name=name, namespace=namespace)
        
        status_summary = f"HPA '{name}' in namespace '{namespace}':\n"
        status_summary += f"  Reference: {hpa.spec.scale_target_ref.kind}/{hpa.spec.scale_target_ref.name}\n"
        status_summary += f"  Min Replicas: {hpa.spec.min_replicas}\n"
        status_summary += f"  Max Replicas: {hpa.spec.max_replicas}\n"
        
        if hpa.status:
            status_summary += f"  Current Replicas: {hpa.status.current_replicas}\n"
            status_summary += f"  Desired Replicas: {hpa.status.desired_replicas}\n"
            
            if hpa.status.current_metrics:
                status_summary += "  Current Metrics:\n"
                for metric in hpa.status.current_metrics:
                    if metric.resource:
                        status_summary += f"    - Resource: {metric.resource.name}, Current: {metric.resource.current.average_value or metric.resource.current.average_utilization} (Target: {hpa.spec.metrics[0].resource.target.average_value or hpa.spec.metrics[0].resource.target.average_utilization})\n"
                    elif metric.external:
                        status_summary += f"    - External: {metric.external.metric_name}, Current: {metric.external.current.average_value} (Target: {hpa.spec.metrics[0].external.target.average_value})\n"
                    elif metric.pods:
                        status_summary += f"    - Pods: {metric.pods.metric_name}, Current: {metric.pods.current.average_value} (Target: {hpa.spec.metrics[0].pods.target.average_value})\n"
            
            if hpa.status.conditions:
                status_summary += "  Conditions:\n"
                for condition in hpa.status.conditions:
                    status_summary += f"    - {condition.type}: {condition.status} (Reason: {condition.reason}, Message: {condition.message})\n"
        
        return status_summary
    except ApiException as e:
        if e.status == 404:
            return f"HPA '{name}' not found in namespace '{namespace}'."
        return f"Error getting HPA status for '{name}': {e}"

def create_kubernetes_pvc(name: str, namespace: str, storage_class: str, size: str, access_modes: list = ['ReadWriteOnce']) -> str:
    """Create a Kubernetes PersistentVolumeClaim (PVC)."""
    try:
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": name},
            "spec": {
                "accessModes": access_modes,
                "storageClassName": storage_class,
                "resources": {
                    "requests": {
                        "storage": size
                    }
                }
            }
        }
        v1.create_namespaced_persistent_volume_claim(body=pvc_manifest, namespace=namespace)
        return f"PVC '{name}' created successfully in namespace '{namespace}' with size {size}."
    except ApiException as e:
        return f"Error creating PVC '{name}': {e}"

def delete_kubernetes_pvc(name: str, namespace: str, confirm: bool = False) -> str:
    """Delete a Kubernetes PersistentVolumeClaim (PVC) by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete PVC '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete pvc {name}'."
        v1.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        return f"PVC '{name}' deleted successfully from namespace '{namespace}'."
    except ApiException as e:
        if e.status == 404:
            return f"PVC '{name}' not found in namespace '{namespace}'."
        return f"Error deleting PVC '{name}': {e}"

def get_kubernetes_pvc(name: str, namespace: str) -> str:
    """Get details of a specific Kubernetes PersistentVolumeClaim (PVC)."""
    try:
        pvc = v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        status = pvc.status.phase
        capacity = pvc.status.capacity.get('storage', 'N/A') if pvc.status.capacity else 'N/A'
        volume = pvc.spec.volume_name or 'Unbound'
        storage_class = pvc.spec.storage_class_name
        return (f"PVC '{name}' in namespace '{namespace}':\n"
                f"  Status: {status}\n"
                f"  Volume: {volume}\n"
                f"  Capacity: {capacity}\n"
                f"  StorageClass: {storage_class}\n"
                f"  Access Modes: {', '.join(pvc.spec.access_modes)}")
    except ApiException as e:
        if e.status == 404:
            return f"PVC '{name}' not found in namespace '{namespace}'."
        return f"Error getting PVC '{name}': {e}"

def list_kubernetes_pvcs(namespace: Optional[str] = None) -> str:
    """List all Kubernetes PersistentVolumeClaims (PVCs) in a given namespace or all namespaces."""
    try:
        if namespace:
            pvcs = [pvc.metadata.name for pvc in v1.list_namespaced_persistent_volume_claim(namespace=namespace).items]
            return f"PVCs in namespace {namespace}: {', '.join(pvcs) if pvcs else 'None'}"
        else:
            pvcs = [pvc.metadata.name for pvc in v1.list_persistent_volume_claim_for_all_namespaces().items]
            return f"All PVCs: {', '.join(pvcs) if pvcs else 'None'}"
    except ApiException as e:
        return f"Error listing PVCs: {e}"

def create_kubernetes_hpa(name: str, namespace: str, scale_target_kind: str, scale_target_name: str, min_replicas: int, max_replicas: int, cpu_utilization: int) -> str:
    """Create a HorizontalPodAutoscaler targeting CPU utilization."""
    try:
        hpa_manifest = {
            "apiVersion": "autoscaling/v1",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": name},
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": scale_target_kind,
                    "name": scale_target_name
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "targetCPUUtilizationPercentage": cpu_utilization
            }
        }
        autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(body=hpa_manifest, namespace=namespace)
        return f"HPA '{name}' created successfully in namespace '{namespace}'."
    except ApiException as e:
        return f"Error creating HPA '{name}': {e}"

def delete_kubernetes_hpa(name: str, namespace: str, confirm: bool = False) -> str:
    """Delete a HorizontalPodAutoscaler by name and namespace."""
    try:
        if not confirm:
            return f"Confirmation required to delete HPA '{name}' in namespace '{namespace}'. Please confirm by saying 'yes, delete hpa {name}'."
        autoscaling_v1.delete_namespaced_horizontal_pod_autoscaler(name=name, namespace=namespace)
        return f"HPA '{name}' deleted successfully from namespace '{namespace}'."
    except ApiException as e:
        if e.status == 404:
            return f"HPA '{name}' not found in namespace '{namespace}'."
        return f"Error deleting HPA '{name}': {e}"

def list_kubernetes_hpas(namespace: Optional[str] = None) -> str:
    """List all HorizontalPodAutoscalers in a given namespace or all namespaces."""
    try:
        if namespace:
            hpas = [hpa.metadata.name for hpa in autoscaling_v1.list_namespaced_horizontal_pod_autoscaler(namespace=namespace).items]
            return f"HPAs in namespace {namespace}: {', '.join(hpas) if hpas else 'None'}"
        else:
            hpas = [hpa.metadata.name for hpa in autoscaling_v1.list_horizontal_pod_autoscaler_for_all_namespaces().items]
            return f"All HPAs: {', '.join(hpas) if hpas else 'None'}"
    except ApiException as e:
        return f"Error listing HPAs: {e}"

def list_kubernetes_network_policies(namespace: str) -> str:
    """List all NetworkPolicies in a given namespace."""
    try:
        policies = [p.metadata.name for p in networking_v1.list_namespaced_network_policy(namespace=namespace).items]
        return f"NetworkPolicies in namespace {namespace}: {', '.join(policies) if policies else 'None'}"
    except ApiException as e:
        return f"Error listing NetworkPolicies: {e}"

resource_api_map = {
    "pod": (v1, "read_namespaced_pod"),
    "deployment": (apps_v1, "read_namespaced_deployment"),
    "service": (v1, "read_namespaced_service"),
    "namespace": (v1, "read_namespace"), # Note: no 'namespaced' for namespace itself
    "node": (v1, "read_node"), # Note: no 'namespaced' for node itself
    "configmap": (v1, "read_namespaced_config_map"),
    "secret": (v1, "read_namespaced_secret"),
    "ingress": (networking_v1, "read_namespaced_ingress"),
    "pvc": (v1, "read_namespaced_persistent_volume_claim"),
    "hpa": (autoscaling_v1, "read_namespaced_horizontal_pod_autoscaler"),
    "networkpolicy": (networking_v1, "read_namespaced_network_policy"),
    # Add more as needed
}

def describe_kubernetes_resource(resource_type: str, name: str, namespace: Optional[str] = None) -> str:
    """
    Get detailed information about a Kubernetes resource (pod, deployment, service, etc.).
    This mimics 'kubectl describe'.
    """
    resource_type = resource_type.lower()
    if resource_type not in resource_api_map:
        return f"Unsupported resource type for description: {resource_type}. Supported types: {', '.join(resource_api_map.keys())}"

    api_client, read_method_name = resource_api_map[resource_type]
    try:
        if "namespaced" in read_method_name:
            if not namespace:
                return f"Namespace is required for resource type '{resource_type}'."
            resource_obj = getattr(api_client, read_method_name)(name=name, namespace=namespace)
        else:
            resource_obj = getattr(api_client, read_method_name)(name=name)

        # Convert the Kubernetes object to a dictionary and then to YAML for readability
        return f"Description of {resource_type} '{name}' in namespace '{namespace or 'N/A'}':\n{yaml.dump(resource_obj.to_dict(), default_flow_style=False)}"
    except ApiException as e:
        if e.status == 404:
            return f"{resource_type} '{name}' not found in namespace '{namespace or 'N/A'}'."
        return f"Error describing {resource_type} '{name}': {e}"
    except Exception as e:
        return f"An unexpected error occurred while describing {resource_type} '{name}': {e}"

def get_kubernetes_node_status(name: str) -> str:
    """Get the status and conditions of a specific Kubernetes Node."""
    try:
        node = v1.read_node_status(name=name)
        
        status_summary = f"Node '{name}' Status:\n"
        
        # Node Conditions
        conditions_str = "No conditions reported."
        if node.status.conditions:
            conditions_list = []
            for c in node.status.conditions:
                conditions_list.append(f"- {c.type}: {c.status} (Reason: {c.reason}, Message: {c.message})")
            conditions_str = "\n".join(conditions_list)
        status_summary += f"  Conditions:\n{conditions_str}\n"
        
        # Addresses
        addresses_str = "No addresses reported."
        if node.status.addresses:
            addresses_list = [f"- {addr.type}: {addr.address}" for addr in node.status.addresses]
            addresses_str = "\n".join(addresses_list)
        status_summary += f"  Addresses:\n{addresses_str}\n"
        
        # Capacity and Allocatable
        if node.status.capacity:
            status_summary += f"  Capacity: {node.status.capacity}\n"
        if node.status.allocatable:
            status_summary += f"  Allocatable: {node.status.allocatable}\n"
            
        return status_summary
    except ApiException as e:
        if e.status == 404:
            return f"Node '{name}' not found."
        return f"Error getting node status for '{name}': {e}"

def get_kubernetes_cluster_status() -> str:
    """Get a high-level status overview of the Kubernetes cluster, including node health."""
    try:
        nodes = v1.list_node().items
        
        total_nodes = len(nodes)
        ready_nodes = 0
        node_summaries = []
        
        for node in nodes:
            node_name = node.metadata.name
            ready_condition = next((c for c in node.status.conditions if c.type == "Ready"), None)
            
            if ready_condition and ready_condition.status == "True":
                ready_nodes += 1
                node_summaries.append(f"- Node '{node_name}': Ready")
            else:
                status = ready_condition.status if ready_condition else "Unknown"
                reason = ready_condition.reason if ready_condition else "N/A"
                node_summaries.append(f"- Node '{node_name}': Not Ready (Status: {status}, Reason: {reason})")
                
        return (f"Kubernetes Cluster Status:\n"
                f"  Total Nodes: {total_nodes}\n"
                f"  Ready Nodes: {ready_nodes}\n"
                f"Node Details:\n" + "\n".join(node_summaries))
    except ApiException as e:
        return f"Error getting cluster status: {e}"

def get_kubernetes_events(namespace: Optional[str] = None, field_selector: Optional[str] = None, limit: int = 50) -> str:
    """
    Get Kubernetes events from a specific namespace or all namespaces.
    Can filter by field selector (e.g., 'involvedObject.name=my-pod').
    Returns the last 'limit' events.
    """
    try:
        if namespace:
            events = v1.list_namespaced_event(namespace=namespace, field_selector=field_selector, limit=limit).items
        else:
            events = v1.list_event_for_all_namespaces(field_selector=field_selector, limit=limit).items

        if not events:
            return f"No events found in {'namespace ' + namespace if namespace else 'all namespaces'}{' with selector ' + field_selector if field_selector else ''}."

        event_strings = []
        for event in events:
            event_strings.append(f"[{event.last_timestamp or event.event_time}] {event.type} {event.reason} ({event.involved_object.kind}/{event.involved_object.name}): {event.message}")
        return "Kubernetes Events:\n" + "\n".join(event_strings)
    except ApiException as e:
        return f"Error getting Kubernetes events: {e}"

def get_kubernetes_pod_logs(name: str, namespace: str = "default", tail_lines: int = 50) -> str:
    """Get the last N lines of logs from a specific Kubernetes pod."""
    try:
        logs = v1.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=tail_lines)
        if not logs.strip():
            return f"No logs found for pod '{name}' in namespace '{namespace}'."
        return f"Last {tail_lines} lines of logs for pod '{name}' in namespace '{namespace}':\n{logs}"
    except ApiException as e:
        if e.status == 404:
            return f"Pod '{name}' not found in namespace '{namespace}'."
        return f"Error getting logs for pod '{name}': {e}"

# A list of all available tools for easy import.
k8s_tools = [
    list_kubernetes_namespaces, get_kubernetes_pod, list_kubernetes_pods, get_kubernetes_pod_logs,
    get_kubernetes_events, get_kubernetes_deployment_status, get_kubernetes_config_map,
    get_kubernetes_secret, create_kubernetes_secret, delete_kubernetes_secret,
    get_kubernetes_ingress, create_kubernetes_ingress, delete_kubernetes_ingress,
    get_kubernetes_node_status, get_kubernetes_cluster_status,
    get_kubernetes_hpa_status, list_kubernetes_hpas, create_kubernetes_hpa, delete_kubernetes_hpa,
    describe_kubernetes_resource,
    create_kubernetes_pod, delete_kubernetes_pod,
    create_kubernetes_namespace, delete_kubernetes_namespace,
    create_kubernetes_deployment, delete_kubernetes_deployment, scale_kubernetes_deployment,
    create_kubernetes_service, delete_kubernetes_service,
    list_kubernetes_services, list_kubernetes_deployments,
    # PVC Tools
    create_kubernetes_pvc, delete_kubernetes_pvc, get_kubernetes_pvc, list_kubernetes_pvcs,
    # Networking Tools
    list_kubernetes_network_policies,
    # I am not including create/get/delete for network policies yet as they are complex.
    # The 'describe' tool can be used for detailed inspection.
]
