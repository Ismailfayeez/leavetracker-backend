import pytz
from rest_framework import serializers


class UserInfoValidation():
    def validate_country(self, country):
        try:
            pytz.country_timezones[country.lower()]
            return country
        except:
            raise serializers.ValidationError(
                "Country code is not a valid one")

    def validate_timezone(self, timezone):
        try:
            pytz.timezone(timezone)
            return timezone
        except:
            raise serializers.ValidationError(
                "Timezone is not a valid one")
