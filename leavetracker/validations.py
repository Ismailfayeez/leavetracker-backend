from leavetracker.models import Team
from rest_framework import serializers
from utilities.error import CustomApiResponseError


class BaseTeamValidation():
    def validate_name(self, name):
        employee = self.context.get('employee')
        if(5 > len(name) or len(name) > 25):
            raise serializers.ValidationError(
                "Name length should be greater than 5 and less than 25")
        queryset = Team.objects.filter(name=name, project=employee.project)
        if self.instance is not None:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError(
                "Team Name already in use.Please Change")
        return name


def validate_my_groups_report_section_id(sections, allowed_sections):
    if sections is None:
        raise CustomApiResponseError(
            data='section parameter not found', status=404)
    try:
        section_params = [int(section_id)
                          for section_id in sections.split(",")]
        if not set(section_params).issubset(set(allowed_sections)):
            raise CustomApiResponseError(
                data='Invalid section parameter', status=400)
        return section_params
    except:
        raise CustomApiResponseError(
            data='Invalid section parameter', status=400)
