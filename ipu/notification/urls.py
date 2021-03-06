from django.conf.urls import url, include
from .views import get_notifications , select_streams , create_notification , submit_issue , select_years , solve_issue , display_issue , display_solution, display_solution_list , mark_issue , notification_detail , truncated_notifications

urlpatterns = [
	url(r'^get_notifications/$', get_notifications, name='get_notifications'),
	url(r'^select_streams/$' , select_streams , name = 'select_streams'),
	url(r'^select_years/$' , select_years , name = 'select_years'),
	url(r'^create_notification/$' , create_notification , name = 'create_notification'),
	url(r'^submit_issue/$' , submit_issue , name = 'submit_issue'),
	url(r'^mark/$' , mark_issue , name = 'mark'),
	url(r'^solve_issue/$' , solve_issue , name = 'solve_issue'),
	url(r'^view_issue/$' , display_issue , name = 'view_issue'),
	url(r'^view_solution_list/$' , display_solution_list , name = 'view_solution_list'),
	url(r'^view_solution/$' , display_solution , name = 'view_solution'),
	url(r'^notification_detail/$' , notification_detail , name = 'notification_detail'),
	url(r'^shorten/$', truncated_notifications, name='shortened_notifications'),
]