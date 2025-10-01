# ChatGPT MCP Connector Firewall Configuration

## Overview

OpenAI uses specific IP address ranges for ChatGPT connectors (formerly plugins/actions). While OpenAI doesn't always maintain a fully public list of these IPs, based on community reports and historical documentation, here are the known IP ranges that should be whitelisted for ChatGPT MCP connectors.

## Known ChatGPT Connector IP Ranges

Based on community reports and OpenAI documentation, these are the IP ranges that have been observed for ChatGPT connections:

### Primary IP Ranges (Confirmed by Community)
```
# Microsoft Azure (US West/Central) - Primary ChatGPT Infrastructure
23.102.140.112/28    # 23.102.140.112 - 23.102.140.127
13.66.11.96/28       # 13.66.11.96 - 13.66.11.111
23.98.142.176/28     # 23.98.142.176 - 23.98.142.191
40.84.180.224/28     # 40.84.180.224 - 40.84.180.239

# Additional reported ranges
76.16.33.0/24        # Reported in late 2023
128.252.147.0/24     # Reported in late 2023
```

### OpenAI Bot/Crawler IPs (Different from connectors, but good to know)
```
# These are for web crawling, not MCP connections
20.42.10.176
172.203.190.128
51.8.102.0
```

## Firewall Configuration

### Option 1: GCP Firewall Rules (Recommended)

Create firewall rules in GCP to allow ChatGPT connections:

```bash
# Create a firewall rule for ChatGPT MCP connections
gcloud compute firewall-rules create allow-chatgpt-mcp \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=23.102.140.112/28,13.66.11.96/28,23.98.142.176/28,40.84.180.224/28,76.16.33.0/24,128.252.147.0/24 \
    --target-tags=mcp-server \
    --description="Allow ChatGPT MCP connector access"

# Apply the tag to your VM
gcloud compute instances add-tags YOUR-VM-NAME \
    --tags=mcp-server \
    --zone=YOUR-ZONE
```

### Option 2: iptables Rules (On the Server)

Add iptables rules directly on your server:

```bash
#!/bin/bash
# Save as: configure-chatgpt-firewall.sh

# ChatGPT MCP IP ranges
CHATGPT_IPS=(
    "23.102.140.112/28"
    "13.66.11.96/28"
    "23.98.142.176/28"
    "40.84.180.224/28"
    "76.16.33.0/24"
    "128.252.147.0/24"
)

# Add rules for HTTPS (port 443)
for IP in "${CHATGPT_IPS[@]}"; do
    iptables -A INPUT -p tcp --dport 443 -s "$IP" -j ACCEPT
    echo "Added rule for $IP"
done

# Save iptables rules
iptables-save > /etc/iptables/rules.v4
```

### Option 3: Nginx IP Whitelisting

Add IP restrictions directly in Nginx configuration:

```nginx
# In your nginx/conf.d/default.conf, add to the ChatGPT location blocks:

# Define allowed IPs for ChatGPT
geo $chatgpt_allowed {
    default 0;
    23.102.140.112/28 1;
    13.66.11.96/28 1;
    23.98.142.176/28 1;
    40.84.180.224/28 1;
    76.16.33.0/24 1;
    128.252.147.0/24 1;
}

# In the ChatGPT SSE endpoint
location = /chatgpt/sse {
    # Check if request is from allowed IP
    if ($chatgpt_allowed = 0) {
        return 403 "Access denied - IP not whitelisted for ChatGPT";
    }
    
    # ... rest of your configuration
}
```

### Option 4: Docker Compose with IP Restrictions

Add IP filtering at the Docker level:

```yaml
# In docker-compose.chatgpt.yml
services:
  nginx-chatgpt:
    # ... existing configuration
    extra_hosts:
      - "host.docker.internal:host-gateway"
    sysctls:
      - net.ipv4.ip_forward=1
    cap_add:
      - NET_ADMIN
```

## Security Best Practices

### 1. Use Multiple Layers
Combine GCP firewall rules with application-level authentication (OAuth) for defense in depth.

### 2. Monitor and Log
Enable logging to track connection attempts:

```bash
# Enable GCP firewall logging
gcloud compute firewall-rules update allow-chatgpt-mcp \
    --enable-logging

# Check Nginx access logs for ChatGPT connections
tail -f /var/log/nginx/chatgpt.access.log | grep -E "23\.102\.|13\.66\.|23\.98\.|40\.84\.|76\.16\.|128\.252\."
```

### 3. Regular Updates
OpenAI may add new IP ranges without notice. Monitor your logs for blocked legitimate requests:

```bash
# Script to monitor for new IPs
#!/bin/bash
# monitor-new-ips.sh

LOG_FILE="/var/log/nginx/access.log"
KNOWN_IPS="chatgpt-known-ips.txt"

# Extract IPs that got 403 errors
grep "403" $LOG_FILE | \
    grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | \
    sort -u | \
    while read IP; do
        if ! grep -q "$IP" "$KNOWN_IPS"; then
            echo "Potential new ChatGPT IP: $IP"
            # Check if it has ChatGPT user agent
            grep "$IP" $LOG_FILE | grep -i "chatgpt\|openai" && echo "$IP might be legitimate"
        fi
    done
```

### 4. Fallback Option: Authentication-Only
If IP whitelisting causes issues, you can rely solely on OAuth authentication:

```nginx
# Remove IP restrictions but keep OAuth
location = /chatgpt/sse {
    # No IP check, rely on OAuth tokens
    # ... rest of configuration
}
```

## Testing the Configuration

### Test from Allowed IPs
```bash
# This should work from ChatGPT
curl -I https://data.forensic-bot.com/chatgpt/health
```

### Test from Blocked IPs
```bash
# This should return 403 from non-whitelisted IPs
curl -I https://data.forensic-bot.com/chatgpt/sse
```

## Important Notes

1. **IP Ranges May Change**: OpenAI occasionally adds new IP ranges. Monitor your logs for legitimate requests being blocked.

2. **Regional Differences**: ChatGPT may use different IPs based on the user's region. The listed IPs are primarily for US-based infrastructure.

3. **OAuth is Primary Security**: IP whitelisting is an additional layer. OAuth 2.0 authentication remains your primary security mechanism.

4. **Testing Required**: After implementing IP restrictions, thoroughly test the connection from ChatGPT to ensure it works.

## Verification with OpenAI

For the most current IP ranges, you should:

1. **Check OpenAI Documentation**: Look for updates at:
   - https://platform.openai.com/docs/actions/production
   - https://platform.openai.com/docs/plugins/production

2. **Contact OpenAI Support**: For Enterprise/Team accounts, OpenAI support may provide current IP ranges.

3. **Monitor Community Forums**: The OpenAI Developer Community often shares updates about new IP ranges.

## Alternative: Domain-Based Filtering (Not Reliable)

NGINX cannot verify the true originating domain of an inbound TCP client. Anycast, CDNs, and intermediate networks mean the source IP rarely maps to a single domain, and request headers like Referer or Origin are client-controlled and can be spoofed. Reverse DNS is also not a proof of control. Therefore, “filter by domain” at the L4/L7 edge is not reliable for MCP connectors.

Recommended instead:

1) OAuth 2.0 required on /sse (implemented)
- The application now rejects /sse requests without a valid Bearer token. This is transport- and network-agnostic and works with Anycast.

2) Restrict redirect URIs to trusted domains (implemented)
- Only ChatGPT/OpenAI/Claude domains are allowed during the OAuth authorize step. Configure via env var:
    - ALLOWED_REDIRECT_HOSTS=chatgpt.com,openai.com,claude.ai,anthropic.com

3) Optional edge guard in NGINX (header-based)
- Block non-HEAD requests to /sse when there's no Authorization: Bearer header AND no shared secret header. Enable with env vars passed to the NGINX container:

Environment variables for NGINX (docker-compose):
```yaml
services:
    nginx:
        environment:
            - MCP_REQUIRE_AUTH=on        # off to disable
            - MCP_SHARED_SECRET=${MCP_SHARED_SECRET} # optional shared secret
```

Nginx snippet already wired in conf.d/default.conf:
```nginx
map $http_authorization $has_auth_header { default 0; ~*^Bearer\s+.+ 1; }
map $http_x_mcp_secret $mcp_secret_ok { default 0; "${MCP_SHARED_SECRET}" 1; }
set $require_auth ${MCP_REQUIRE_AUTH};

location = /chatgpt/sse {
    if ($request_method != HEAD) {
        if ($require_auth = on) {
            if ($has_auth_header = 0) {
                if ($mcp_secret_ok = 0) { return 401; }
            }
        }
    }
    # ... existing SSE proxy config
}
```

4) Stronger options (consider)
- mTLS: require client certificates; share certs with OpenAI/Anthropic if supported.
- auth_request: central auth service that validates tokens or HMAC.
- Zero Trust proxies: Cloudflare Access / Google IAP in front of NGINX.

## Conclusion

While IP whitelisting adds a security layer, remember:
- Domain-based filtering at the edge isn’t reliable.
- OAuth 2.0 is your primary control and now enforced on /sse.
- Optionally enable the NGINX header guard for early rejection.
- For highest assurance, adopt mTLS or a Zero Trust access proxy.

Start with the documented IP ranges above, monitor your logs, and adjust as needed based on actual ChatGPT connection attempts.