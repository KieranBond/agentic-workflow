#!/usr/bin/env python3
"""Sentry API helper for fetching issue details and events.

Reads config from ~/.sentryclirc. Supports:
  - Fetching issue metadata
  - Fetching latest event with stack trace
  - Fetching event frequency distribution by context field
  - Listing issues for a project with filters
"""
import argparse
import configparser
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


def load_config() -> tuple[str, str]:
    """Return (base_url, token) from ~/.sentryclirc."""
    rc = Path.home() / ".sentryclirc"
    if not rc.exists():
        print("Error: ~/.sentryclirc not found", file=sys.stderr)
        print(
            "Create it with:\n"
            "  [defaults]\n"
            "  url=https://your-sentry.example.com/\n\n"
            "  [auth]\n"
            "  token=sntryu_...",
            file=sys.stderr,
        )
        sys.exit(1)
    cfg = configparser.ConfigParser()
    cfg.read(rc)
    url = cfg.get("defaults", "url").rstrip("/")
    token = cfg.get("auth", "token")
    return url, token


def api_get(base_url: str, token: str, path: str) -> Any:
    """GET a Sentry API endpoint and return parsed JSON."""
    url = f"{base_url}{path}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError:
        print("Request timed out", file=sys.stderr)
        sys.exit(1)


def parse_issue_url(url: str) -> tuple[str, str]:
    """Extract (org_slug, issue_id) from a Sentry issue URL."""
    m = re.search(
        r"/organizations/([^/]+)/issues/(\d+)", url
    )
    if not m:
        print(f"Error: cannot parse issue URL: {url}", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2)


def get_event_context(event: dict[str, Any]) -> dict[str, Any]:
    """Return event context map supporting both context/contexts keys."""
    return event.get("context") or event.get("contexts") or {}


def cmd_issue(args: argparse.Namespace) -> None:
    """Fetch and display issue metadata + latest event details."""
    base_url, token = load_config()
    org, issue_id = parse_issue_url(args.url)

    issue = api_get(
        base_url, token,
        f"/api/0/organizations/{org}/issues/{issue_id}/",
    )
    print("=== Issue ===")
    for key in [
        "title", "culprit", "count", "firstSeen",
        "lastSeen", "level", "status",
    ]:
        if key in issue:
            print(f"  {key}: {issue[key]}")

    event = api_get(
        base_url, token,
        f"/api/0/organizations/{org}/issues/{issue_id}/events/latest/",
    )
    print("\n=== Latest Event Context ===")
    ctx = get_event_context(event)
    for k, v in ctx.items():
        print(f"  {k}: {v}")

    print("\n=== Tags ===")
    for tag in event.get("tags", []):
        print(f"  {tag['key']}: {tag['value']}")

    print("\n=== Entries ===")
    for entry in event.get("entries", []):
        etype = entry.get("type")
        if etype == "exception":
            for val in entry["data"]["values"]:
                print(
                    f"Exception: {val.get('type')} "
                    f"- {val.get('value')}"
                )
                frames = (
                    val.get("stacktrace", {}).get("frames") or []
                )
                for frame in frames[-10:]:
                    fname = frame.get("filename", "?")
                    lineno = frame.get("lineNo", "?")
                    func = frame.get("function", "?")
                    print(f"  {fname}:{lineno} in {func}")
        elif etype == "message":
            data = entry["data"]
            msg = data.get("formatted") or data.get("message")
            print(f"Message: {msg}")
        elif etype == "breadcrumbs":
            crumbs = entry["data"].get("values", [])[-5:]
            for bc in crumbs:
                cat = bc.get("category", "")
                msg = bc.get("message", "")
                print(f"Breadcrumb: [{cat}] {msg}")


def cmd_events(args: argparse.Namespace) -> None:
    """Fetch multiple events and show context field distribution."""
    base_url, token = load_config()
    org, issue_id = parse_issue_url(args.url)
    limit = args.limit

    events = api_get(
        base_url, token,
        f"/api/0/organizations/{org}/issues/{issue_id}"
        f"/events/?full=true&limit={limit}",
    )

    if args.field:
        from collections import Counter
        counts: Counter[str] = Counter()
        for evt in events:
            ctx = get_event_context(evt)
            val = ctx.get(args.field, "MISSING")
            counts[str(val)] += 1
        print(f"Distribution of context.{args.field} "
              f"({len(events)} events):")
        for val, count in counts.most_common():
            print(f"  {count:5d}  {val}")
    else:
        for i, evt in enumerate(events[:10]):
            print(f"--- Event {i} ({evt.get('dateCreated')}) ---")
            ctx = get_event_context(evt)
            for k, v in ctx.items():
                print(f"  {k}: {v}")
            print()


def cmd_list(args: argparse.Namespace) -> None:
    """List issues for a project."""
    base_url, token = load_config()
    org = args.org
    project = args.project
    query = args.query

    params = f"query={urllib.parse.quote(query)}&limit={args.limit}"
    if args.environment:
        params += f"&environment={args.environment}"

    issues = api_get(
        base_url, token,
        f"/api/0/projects/{org}/{project}/issues/?{params}",
    )
    if not issues:
        print("No issues found matching the query.")
        return

    print(f"{'ID':>6}  {'Count':>7}  {'Last Seen':25s}  Title")
    print("-" * 90)
    for issue in issues:
        print(
            f"{issue['id']:>6}  "
            f"{issue.get('count', '?'):>7}  "
            f"{issue.get('lastSeen', '?'):25s}  "
            f"{issue.get('title', '?')[:60]}"
        )
    print(f"\n{len(issues)} issues returned.")
    print(
        f"View in browser: {base_url}/organizations/{org}"
        f"/issues/?project={project}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sentry API helper"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_issue = sub.add_parser(
        "issue", help="Fetch issue details from a URL"
    )
    p_issue.add_argument("url", help="Sentry issue URL")
    p_issue.set_defaults(func=cmd_issue)

    p_events = sub.add_parser(
        "events",
        help="Fetch events and optionally aggregate a field",
    )
    p_events.add_argument("url", help="Sentry issue URL")
    p_events.add_argument(
        "--field", help="Context field to aggregate"
    )
    p_events.add_argument(
        "--limit", type=int, default=100,
        help="Number of events to fetch",
    )
    p_events.set_defaults(func=cmd_events)

    p_list = sub.add_parser(
        "list", help="List issues for a project"
    )
    p_list.add_argument(
        "--org", default="sentry", help="Organization slug"
    )
    p_list.add_argument(
        "--project", required=True, help="Project slug"
    )
    p_list.add_argument(
        "--query",
        default="is:unresolved issue.priority:[high, medium]",
        help="Issue search query",
    )
    p_list.add_argument(
        "--environment", default="live",
        help="Environment filter",
    )
    p_list.add_argument(
        "--limit", type=int, default=25,
        help="Max issues to return",
    )
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    import urllib.parse
    main()
