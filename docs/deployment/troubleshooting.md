# Deployment Troubleshooting Guide

> TODO: Extract from archived bug reports and deployment experience

## Common Issues

### Docker Issues

#### Container Won't Start
<!-- TODO: Startup issues -->
```bash
# Debug commands
docker logs <container>
docker inspect <container>
```

#### Permission Errors
<!-- TODO: File permission issues -->

#### Network Issues
<!-- TODO: Port conflicts, connectivity -->

### Kubernetes Issues

#### Pod CrashLoopBackOff
<!-- TODO: Common causes -->

#### ImagePullBackOff
<!-- TODO: Registry issues -->

#### Resource Limits
<!-- TODO: OOMKilled, CPU throttling -->

### API Issues

#### 500 Internal Server Error
<!-- TODO: Common causes -->

#### Timeout Errors
<!-- TODO: Slow requests -->

#### Connection Refused
<!-- TODO: Service not running -->

### Performance Issues

#### Slow Response Times
<!-- TODO: Debugging steps -->

#### High Memory Usage
<!-- TODO: Memory leaks -->

#### Cache Issues
<!-- TODO: Redis problems -->

## Debugging Tools

### Logs
```bash
# Docker logs
docker logs -f <container>

# Kubernetes logs
kubectl logs -f <pod>
```

### Shell Access
```bash
# Docker
docker exec -it <container> bash

# Kubernetes
kubectl exec -it <pod> -- bash
```

### Health Checks
```bash
# Check health
curl http://localhost:8000/health
```

## Known Issues

### NEDC Path Resolution
<!-- TODO: Extract from ALPHA_WRAPPER_P0_BUG.md -->

### Algorithm Specific Issues
<!-- TODO: Extract from bug reports -->

## FAQ

### Q: Container exits immediately
<!-- TODO: Solution -->

### Q: Can't connect to Redis
<!-- TODO: Solution -->

### Q: API returns wrong results
<!-- TODO: Parity checking -->

## Getting Help

### Logs to Collect
1. Container/pod logs
2. System metrics
3. Configuration files
4. Error messages

### Support Channels
- GitHub Issues
- Documentation
- Community

## Related
- [Docker Deployment](docker.md)
- [Kubernetes Deployment](kubernetes.md)
- [Configuration](configuration.md)
- [Monitoring](monitoring.md)