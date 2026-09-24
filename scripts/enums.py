from enum import StrEnum

class AccessEnum(StrEnum):
    ALL_ACCESS = 'all-access'
    DESKTOP = 'desktop'
    MOBILE_APP = 'mobile-app'
    MOBILE_WEB = 'mobile-web'


class AgentEnum(StrEnum):
    ALL_AGENTS = 'all-agents'
    USER = 'user'
    SPIDER = 'spider'
    AUTOMATED = 'automated'

class GranularityEnum(StrEnum):
    HOURLY = 'hourly'
    DAILY = 'daily'
    MONTHLY = 'monthly'


