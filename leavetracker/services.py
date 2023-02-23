from .models import LeaveRequest
from django.db.models.aggregates import Max, Min
from .query_methods import get_latest_leave_request_no


def generateOrderNumber(**kwargs):
    inc = 1
    if kwargs.get('increment'):
        inc = inc + kwargs.get('increment')
    new_request_number = 1000
    max_request_number = LeaveRequest.objects.aggregate(
        count=Max('request_number'))
    if not max_request_number["count"]:
        return new_request_number
    new_request_number = max_request_number["count"]+inc
    if LeaveRequest.objects.filter(request_number=new_request_number).exists():
        return generateOrderNumber(increment=inc)
    return new_request_number


def validate_new_request_number(request_Number, project):
    if not LeaveRequest.objects.filter(request_number=request_Number, employee__project=project).exists():
        return request_Number
    else:
        return validate_new_request_number(request_Number+1)


def generate_request_number(project):
    existing_req_no = get_latest_leave_request_no(project)
    inc = 1
    new_req_no = existing_req_no+inc
    return validate_new_request_number(new_req_no, project)
