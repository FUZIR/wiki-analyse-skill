import json
import os
import urllib.error
import urllib.request
from datetime import date
from urllib.parse import quote

from enums import AccessEnum, AgentEnum, GranularityEnum

BASE_URL = os.environ.get('WIKI_BASE_URL', 'https://wikimedia.org/api/rest_v1/metrics/pageviews')
# Wikimedia blocks the default Python-urllib User-Agent; see https://meta.wikimedia.org/wiki/User-Agent_policy
USER_AGENT = os.environ.get('WIKI_USER_AGENT', 'wiki-analyser-skill/0.1')


class WikiApiError(Exception):
    def __init__(self, status: int, detail: str, url: str):
        super().__init__(f'{status} {detail} ({url})')
        self.status = status
        self.detail = detail
        self.url = url


def _hourly(d: date) -> str:
    return d.strftime('%Y%m%d') + '00'


class WikiClient:
    def __init__(self, base_url: str = BASE_URL, user_agent: str = USER_AGENT, timeout: float = 30):
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.timeout = timeout

    def _get(self, *parts: str) -> dict:
        url = '/'.join([self.base_url, *(quote(str(p), safe='') for p in parts)])
        request = urllib.request.Request(url, headers={'User-Agent': self.user_agent, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            try:
                body = json.load(e)
                detail = body.get('detail') or body.get('title') or e.reason
            except ValueError:
                detail = e.reason
            raise WikiApiError(e.code, str(detail), url) from e

    def get_page_views(self, project: str, access: AccessEnum, agent: AgentEnum, granularity: GranularityEnum,
                       start: date, end: date) -> list[dict]:
        """Total views of a project; use project='all-projects' for all Wikimedia projects."""
        data = self._get('aggregate', project, access.value, agent.value, granularity.value, _hourly(start), _hourly(end))
        return data['items']

    def get_page_views_by_country(self, project: str, access: AccessEnum, year: int, month: int) -> list[dict]:
        """Countries ranked by views for a month. Views are bucketed ranges, `views_ceil` is the upper bound."""
        data = self._get('top-by-country', project, access.value, f'{year:04d}', f'{month:02d}')
        return data['items'][0]['countries']

    def get_page_views_for_page(self, project: str, access: AccessEnum, agent: AgentEnum, article: str,
                                granularity: GranularityEnum, start: date, end: date) -> list[dict]:
        data = self._get('per-article', project, access.value, agent.value, article.replace(' ', '_'),
                         granularity.value, _hourly(start), _hourly(end))
        return data['items']

    def get_page_views_for_editor(self, user_central_id: int, granularity: GranularityEnum,
                                  start: date, end: date) -> list[dict]:
        """Views of pages edited by a user; granularity is daily or monthly."""
        data = self._get('v3', 'per_editor', user_central_id, granularity.value,
                         start.strftime('%Y%m%d'), end.strftime('%Y%m%d'))
        return data['items']

    def list_most_viewed(self, project: str, access: AccessEnum, year: int, month: int,
                         day: int | None = None) -> list[dict]:
        """Top 1000 articles for a day, or for the whole month when day is None."""
        day_part = 'all-days' if day is None else f'{day:02d}'
        data = self._get('top', project, access.value, f'{year:04d}', f'{month:02d}', day_part)
        return data['items'][0]['articles']

    def list_most_viewed_by_country(self, country: str, access: AccessEnum, year: int, month: int,
                                    day: int) -> list[dict]:
        """Top articles across all projects for an ISO 3166-1 alpha-2 country code."""
        data = self._get('top-per-country', country.upper(), access.value, f'{year:04d}', f'{month:02d}', f'{day:02d}')
        return data['items'][0]['articles']

    def list_most_viewed_for_editor(self, user_central_id: int, start: date, end: date) -> list[dict]:
        """Top pages edited by a user, per month (only monthly granularity is supported)."""
        data = self._get('v3', 'top_pages_per_editor', user_central_id, GranularityEnum.MONTHLY.value,
                         start.strftime('%Y%m%d'), end.strftime('%Y%m%d'))
        return data['items']
