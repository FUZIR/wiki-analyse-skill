import argparse
import json
import sys
from datetime import date, datetime

from enums import AccessEnum, AgentEnum, GranularityEnum
from wiki_client import WikiApiError, WikiClient


def _month(value: str) -> date:
    return datetime.strptime(value, '%Y-%m').date()


def _add_access(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--access', type=AccessEnum, default=AccessEnum.ALL_ACCESS, choices=list(AccessEnum))


def _add_agent(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--agent', type=AgentEnum, default=AgentEnum.USER, choices=list(AgentEnum))


def _add_range(parser: argparse.ArgumentParser, granularities=tuple(GranularityEnum)) -> None:
    parser.add_argument('--granularity', type=GranularityEnum, default=GranularityEnum.DAILY, choices=granularities)
    parser.add_argument('--start', type=date.fromisoformat, required=True, help='YYYY-MM-DD, inclusive')
    parser.add_argument('--end', type=date.fromisoformat, required=True, help='YYYY-MM-DD, inclusive')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='wiki_cli.py', description=__doc__)
    parser.add_argument('--limit', type=int, help='return only the first N items')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('views', help='total views of a project over time')
    p.add_argument('--project', default='en.wikipedia.org', help="e.g. en.wikipedia.org or 'all-projects'")
    _add_access(p)
    _add_agent(p)
    _add_range(p)

    p = sub.add_parser('article', help='views of a single article over time')
    p.add_argument('title', help="article title, e.g. 'Albert Einstein'")
    p.add_argument('--project', default='en.wikipedia.org')
    _add_access(p)
    _add_agent(p)
    _add_range(p)

    p = sub.add_parser('countries', help='countries ranked by views of a project for a month')
    p.add_argument('--project', default='en.wikipedia.org', help="e.g. en.wikipedia.org or 'all-projects'")
    p.add_argument('--month', type=_month, required=True, help='YYYY-MM')
    _add_access(p)

    p = sub.add_parser('top', help='most viewed articles of a project for a day or a whole month')
    p.add_argument('--project', default='en.wikipedia.org')
    when = p.add_mutually_exclusive_group(required=True)
    when.add_argument('--date', type=date.fromisoformat, help='YYYY-MM-DD')
    when.add_argument('--month', type=_month, help='YYYY-MM')
    _add_access(p)

    p = sub.add_parser('top-country', help='most viewed articles (all projects) in a country for a day')
    p.add_argument('country', help='ISO 3166-1 alpha-2 code, e.g. DE')
    p.add_argument('--date', type=date.fromisoformat, required=True, help='YYYY-MM-DD')
    _add_access(p)

    p = sub.add_parser('editor-views', help="views of pages edited by a user (central user id)")
    p.add_argument('user_id', type=int)
    _add_range(p, (GranularityEnum.DAILY, GranularityEnum.MONTHLY))

    p = sub.add_parser('editor-top', help='most viewed pages edited by a user, per month')
    p.add_argument('user_id', type=int)
    p.add_argument('--start', type=date.fromisoformat, required=True, help='YYYY-MM-DD, first month')
    p.add_argument('--end', type=date.fromisoformat, required=True, help='YYYY-MM-DD, last month')

    return parser


def run(args: argparse.Namespace, client: WikiClient) -> list[dict] | None:
    match args.command:
        case 'views':
            return client.get_page_views(args.project, args.access, args.agent, args.granularity, args.start, args.end)
        case 'article':
            return client.get_page_views_for_page(args.project, args.access, args.agent, args.title,
                                                  args.granularity, args.start, args.end)
        case 'countries':
            return client.get_page_views_by_country(args.project, args.access, args.month.year, args.month.month)
        case 'top':
            day = args.date or args.month
            return client.list_most_viewed(args.project, args.access, day.year, day.month,
                                           args.date.day if args.date else None)
        case 'top-country':
            return client.list_most_viewed_by_country(args.country, args.access, args.date.year, args.date.month,
                                                      args.date.day)
        case 'editor-views':
            return client.get_page_views_for_editor(args.user_id, args.granularity, args.start, args.end)
        case 'editor-top':
            return client.list_most_viewed_for_editor(args.user_id, args.start, args.end)
    return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        items = run(args, WikiClient())
    except WikiApiError as e:
        json.dump({'error': e.detail, 'status': e.status, 'url': e.url}, sys.stderr, ensure_ascii=False)
        sys.stderr.write('\n')
        return 1
    except OSError as e:
        json.dump({'error': str(e)}, sys.stderr, ensure_ascii=False)
        sys.stderr.write('\n')
        return 1
    if args.limit is not None:
        items = items[:args.limit]
    json.dump(items, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
