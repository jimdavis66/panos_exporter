def dedupe_metrics(metrics):
    """Deduplicate Prometheus metric strings by metric name and label set."""
    seen = set()
    deduped = []
    for m in metrics:
        lines = m.split("\n")
        metric_line = next((line for line in lines if line and not line.startswith("#")), None)
        if metric_line:
            metric_name = metric_line.split("{")[0]
            label_str = metric_line.split("{")[1].split("}")[0] if "{" in metric_line else ""
            key = (metric_name, label_str)
            if key not in seen:
                seen.add(key)
                deduped.append(m)
    return deduped


def parse_route_category_metrics(entry, metric_prefix, device, prometheus_metric):
    """
    Parse All-Routes, Static-Routes, etc. child elements into gauge metrics.
    """
    metrics = []
    for category_elem in entry:
        category = category_elem.tag.replace("-", "_").lower()
        for field_elem in category_elem:
            text = (field_elem.text or "").strip()
            if not text:
                continue
            try:
                value = int(text)
            except ValueError:
                continue
            field = field_elem.tag.replace("-", "_").lower()
            metrics.append(
                prometheus_metric(
                    metric=f"{metric_prefix}_{field}",
                    value=value,
                    device=device,
                    help_text=f"Routing {category} {field}",
                    labels={"category": category},
                )
            )
    return metrics
