"""
URL configuration for Tournado project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from home import views as home_views
from users import views as users_views
from tournaments import views as tourn_views
from schedules import views as sched_views
from leagues import views as league_views
from orders import views as order_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', home_views.HomeView.as_view(), name="home"),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name="login"),
    path('logout/', users_views.LogoutView, name='logout'),
    path('account/', home_views.AccountView, name='account'),
    path('user/new/', home_views.UserCreateView.as_view(), name='user-create'),
    path('profile/<int:pk>/', users_views.ProfileView.as_view(), name='profile'),
    path('tourn-list/', home_views.TournFilterView.as_view(), name='tourn-list'),
    path('user-list/', home_views.UserFilterView.as_view(), name='user-list'),
    path('tourn/new/', tourn_views.TournCreateView.as_view(), name='tourn-create'),
    path('tourn/<int:pk>/', tourn_views.TournDetailView.as_view(), name='tourn-detail'),
    path('tourn/<int:pk>/delete/', tourn_views.TournDeleteView.as_view(), name='tourn-delete'),
    path('tourn/<int:pk>/update/', tourn_views.TournUpdateView.as_view(), name='tourn-update'),
    path('account/tourn-list/', tourn_views.TournUserView, name='user-tourn-list'),
    path('account/tourn-list/search-past/', tourn_views.search_bar_past, name='past-user-tourn-search'),
    path('account/tourn-list/search-future/', tourn_views.search_bar_future, name='future-user-tourn-search'),
    path('account/league-list/', league_views.LeagueUserView, name='user-league-list'),
    path('account/tourn/<int:pk>/', tourn_views.TournUserDetailView.as_view(), name='user-tourn-detail'),
    path('account/tourn/<int:pk>/customise', tourn_views.TournCustomiseView.as_view(), name='user-tourn-customise'),
    path('account/league/<int:pk>/', league_views.LeagueUserDetailView.as_view(), name='user-league-detail'),
    path('account/entry-list/', tourn_views.EntryUserView, name='user-entry-list'),
    path('account/entry-list/search-past-entries/', tourn_views.search_past_entries, name='past-user-entry-search'),
    path('account/entry-list/search-future-entries/', tourn_views.search_future_entries, name='future-user-entry-search'),
    path('entry/new/<int:pk>/', tourn_views.EntryCreateView.as_view(), name='entry-create'),
    path('entry/<int:pk>/update/', tourn_views.EntryUpdateView.as_view(), name='entry-update'),
    path('entry/<int:pk>/delete/', tourn_views.EntryDeleteView.as_view(), name='entry-delete'),
    path('entry/<int:pk>/request-delete/', tourn_views.EntryRequestDelete, name="entry-request-delete"),
    path('entry/<int:pk>/results/', home_views.EntryStatsView.as_view(), name='entry-stats'),
    path('schedule/<int:pk>/', sched_views.ScheduleCreateView.as_view(), name='schedule-create'),
    path('schedule/<int:pk>/publish/', sched_views.publish_schedule, name='schedule-publish'),
    path('schedule/<int:pk>/publish/umpire/', sched_views.publish_umpire_schedule, name='schedule-publish-umpire'),
    path('schedule/<int:pk>/detail/', sched_views.SchedulePDFView.as_view(), name='schedule-pdf'),
    path('schedule/<int:pk>/pdf/', sched_views.PDFView.as_view(), name='pdf'),
    path('umpire-schedule/<int:pk>/pdf/', sched_views.UmpirePDFView.as_view(), name='umpire-pdf'),
    path('match-table/<int:pk>/', tourn_views.MatchTableView.as_view(), name='match-table'),
    path('match-list/<int:pk>/', tourn_views.MatchListView.as_view(), name='match-list'),
    path('match/<int:pk>/result/', tourn_views.MatchUpdateView.as_view(), name='match-result'),
    path('match/<int:pk>/update/', tourn_views.MatchKnockoutUpdateView.as_view(), name='match-update'),
    path('live-score/<int:pk>/', home_views.LiveScoreView.as_view(), name='live-score'),
    path('live-events/', home_views.LiveEventView.as_view(), name='live-events'),
    path('past-score/<int:pk>/', home_views.PastScoreView.as_view(), name='past-score'),
    path('past-events/', home_views.PastEventView.as_view(), name='past-events'),
    path('league-list/', home_views.LeagueFilterView.as_view(), name='league-list'),
    path('league/new/', league_views.LeagueCreateView.as_view(), name='league-create'),
    path('league/<int:pk>/', league_views.LeagueDetailView.as_view(), name='league-detail'),
    path('league/<int:pk>/update/', league_views.LeagueUpdateView.as_view(), name='league-update'),
    path('league/<int:pk>/delete/', league_views.LeagueDeleteView.as_view(), name='league-delete'),
    path('league/<int:pk>/publish/', league_views.LeaguePublishView.as_view(), name='league-publish'),
    path('league-entry/new/<int:pk>/', league_views.LeagueEntryCreateView.as_view(), name='league-entry-create'),
    path('league-entry/<int:pk>/update/', league_views.LeagueEntryUpdateView.as_view(), name='league-entry-update'),
    path('league-entry/<int:pk>/delete/', league_views.LeagueEntryDeleteView.as_view(), name='league-entry-delete'),
    path('league-entry/<int:pk>/results/', home_views.LeagueEntryStatsView.as_view(), name='league-entry-stats'),
    path('league-schedule/<int:pk>/', sched_views.LeagueScheduleCreateView.as_view(), name='league-schedule-create'),
    path('league-match-list/<int:pk>/', league_views.LeagueMatchFilterView.as_view(), name='league-match-list'),
    path('league/<int:pk>/match-list', league_views.LeagueMatchListView.as_view(), name='league-match-list-normal'),
    path('league-match/<int:pk>/update/', league_views.LeagueMatchUpdateView.as_view(), name='league-match-update'),
    path('league-match/<int:pk>/result/', league_views.LeagueMatchResultView.as_view(), name='league-match-result'),
    path('league-live-score/<int:pk>/', home_views.LeagueCurrentScoreView.as_view(), name='league-live-score'),
    path('drag-drop/<int:pk>/', sched_views.DragDropView.as_view(), name='drag-drop'),
    path('task-assign/<str:matchOne_id>/<str:matchTwo_id>/', sched_views.ChangeSheetAssign.as_view(), name='change_sheet_assign'),
    path('order/create/<int:pk>/', order_views.auto_create_order_view, name='order-create'),
    path('order/update/<int:pk>/', order_views.OrderUpdateView.as_view(), name='update-order'),
    path('delete/<int:pk>/', order_views.delete_order, name='delete-order'),
    path('submit/<int:pk>/', order_views.submit_order, name='submit-order'),
    path('invoice/<int:pk>/', order_views.invoice_tourn, name='invoice-tourn'),
    path('order-list/<int:pk>/', order_views.UserEntryListView.as_view(), name='order-list'),
    path('ajax/add-product/<int:pk>/<int:dk>/', order_views.ajax_add_product, name='ajax-add'),
    path('ajax/modify-product/<int:pk>/', order_views.ajax_modify_order_item, name='ajax-modify'),
    path('invoice/<int:pk>/pdf/', order_views.InvoicePdf, name='invoice-hf'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),   
    path('past-events/search/', home_views.search_bar, name='past-tourn-search'),
    path('past-events/search-league/', home_views.search_bar_leagues, name='past-league-search'),
    path('entry-assign/<int:pk>/', tourn_views.AssignEntryView.as_view(), name='entry_assign_div'),
    path('entry-assign-clear/<int:pk>/', tourn_views.AssignEntryClearView.as_view(), name='entry_assign_clear'),
    path('entry-assign-auto/<int:pk>/', tourn_views.AssignEntryAutoView.as_view(), name='entry_assign_auto'),
    path('unassign-check/<int:pk>/', tourn_views.UnassignCheckView.as_view(), name='unassign-check'),
    path('entry-assign/<str:emp_id>/<str:task_id>/', tourn_views.ChangeEntryDivision.as_view(), name='change_entry_div'),
    path('pitches-change/', sched_views.pitches_change, name='pitches-change'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)