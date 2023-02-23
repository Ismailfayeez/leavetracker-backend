from leavetracker.models import Role, Domain, Team
from rest_framework import serializers


class BaseTeamValidation():
    def validate_name(self, name):
        project_id = self.context.get('project_id')

        if(5 > len(name) or len(name) > 25):
            raise serializers.ValidationError(
                "Name length should be greater than 5 and less than 25")

        if Team.objects.filter(name=name, project=project_id).exists():
            print(project_id)
            raise serializers.ValidationError(
                "Team Name already in use.Please Change")
        return name
