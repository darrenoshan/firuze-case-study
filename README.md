# مستندات استقرار پروژه


**توجه:** این پروژه بر روی یک **کلاستر چند-مستر کوبرنتیز** با پیکربندی **ETCD خارجی** جهت دسترس‌پذیری و پایداری بالا مستقر شده است.

پیش از آغاز استقرار، یک API ساده در پوشه `app/` قرار داده شده است.

**نکته:** فرآیند ساخت ایمیج کانتینر در این مستند پوشش داده نشده و فرض بر این است که از طریق **GitLab CI/CD** انجام شده و ایمیج نهایی به **ریجستری محلی** ارسال شده است.

---

## وظیفه ۱: استقرار یک میکروسرویس ساده

ابتدا جهت مجزا سازی و مدیریت بهتر یک **Namespace** جدید ساخته میشود.
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: proj-firuze-myapp
```

برای اسقرار برنامه یک **Deployment Resource** با مشخصات زیر تعریف میکنیم.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  namespace: proj-firuze-myapp
  name: myapp
spec:
  replicas: 4
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: reg.lab.local:1082/images/myapp:v0.3
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /v1/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

در ادامه جهت دسترسی به پادها، از **Service Resource** استفاده میکنیم.

```yaml
kind: Service
apiVersion: v1
metadata:
  name: myapp-svc
  namespace: proj-firuze-myapp
  labels:
    app: myapp
spec:
  selector:
    app: myapp
  type: ClusterIP
  ports:
  - name: myapp-port
    port: 8080
    targetPort: 8080
```

نمونه خروجی:

![alt text](<https://raw.githubusercontent.com/darrenoshan/firuze-case-study/refs/heads/main/res1.png>)

---

## وظیفه ۲: اکسپوز کردن اپلیکیشن

برای در دسترس بودن سرویس از خارج از کلاستر، از **Ingress Resource** با استفاده از NGINX Ingress Controller استفاده میکنیم.

برای برنامه ایجاد شده دامنه myapp.lab.local در نظر گرفته شده است.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  namespace: proj-firuze-myapp
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.lab.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-svc
            port:
              number: 8080
```

### خروجی:

![alt text](<https://raw.githubusercontent.com/darrenoshan/firuze-case-study/refs/heads/main/res2.png>)
![alt text](<https://raw.githubusercontent.com/darrenoshan/firuze-case-study/refs/heads/main/res3.png>)

---

## وظیفه ۳: مانیتورینگ میکروسرویس

مانیتورینگ از طریق **Prometheus Stack** انجام می‌شود:

اپلیکیشن، متریک‌ها را در آدرس `/metrics` ارائه میدهد.
برای مانیتور کردن برنامه، یک `ServiceMonitor`  تعریف میکنیم تا از طریق آن Prometheus بتواند برنامه را مانیتور کند.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
  namespace: prometheus
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: myapp
  namespaceSelector:
    matchNames:
      - proj-firuze-myapp
  endpoints:
  - port: myapp-port
    path: /metrics
    interval: 15s
```

![alt text](<https://raw.githubusercontent.com/darrenoshan/firuze-case-study/refs/heads/main/res4.png>)


**Grafana** برای نمایش متریک‌ها از طریق داشبوردهای اختصاصی استفاده می‌شود.
![alt text](<https://raw.githubusercontent.com/darrenoshan/firuze-case-study/refs/heads/main/res5.png>)

```json
{
    "title": "Firuze Myapp Dashboard",
    "panels": [
      {
        "type": "timeseries",
        "title": "http_requests_total rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "refId": "A"
          }
        ],
        "datasource": "Prometheus",
        "fieldConfig": {
          "defaults": {
            "unit": "req/s"
          }
        },
        "gridPos": {
          "h": 9,
          "w": 24,
          "x": 0,
          "y": 0
        }
      }
    ],
    "schemaVersion": 36,
    "version": 1,
    "uid": "test-dashboard"
  }
  
```

