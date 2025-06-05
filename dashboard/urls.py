from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),  # Landing page URL pattern
    path('login/', views.login_view, name='login'),  # Add this line for login
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    path('users/', views.users, name='users'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    # Add these new URLs for zones
    path('api/zones/<int:zone_id>/cells/', views.get_zone_cells, name='get_zone_cells'),
    path('get-zones/', views.get_zones, name='get_zones'),  # Add this line for zone loading
    
    # Change this line from:
    path('zones/', views.zones, name='zones_dashboard'),
    
    # To:
    path('zones/', views.zones, name='zones'),
    path('zones/create/', views.create_zone, name='create_zone'),
    path('zones/edit/<int:zone_id>/', views.edit_zone, name='edit_zone'),
    path('zones/delete/<int:zone_id>/', views.delete_zone, name='delete_zone'),
    # Add these new URLs for cells
    path('cells/', views.cells_view, name='cells'),  # Add this URL pattern
    # Change these lines from:
    path('cells/create/', views.create_cell, name='create_cell'),
    path('cells/edit/<int:cell_id>/', views.edit_cell, name='edit_cell'),
    path('cells/delete/<int:cell_id>/', views.delete_cell, name='delete_cell'),
    path('issues/', views.issues, name='issues'),
    # Add these new URLs for cell management
    path('cell-members/', views.cell_members, name='cell_members'),
    path('cell-issues/', views.cell_issues, name='cell_issues'),
    path('zone/issues/', views.zone_issues_view, name='zone_issues'),
    path('api/issues/<int:issue_id>/details/', views.issue_details, name='issue_details'),
    path('api/issues/<int:issue_id>/approve/', views.approve_issue, name='approve_issue'),
    path('api/issues/<int:issue_id>/reject/', views.reject_issue, name='reject_issue'),
    path('api/issues/<int:issue_id>/comment/', views.add_comment, name='add_comment'),
    # settings page
    path('settings/', views.user_settings, name='settings'),  # Updated to use user_settings view
    path('update_profile/', views.update_profile, name='update_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('update_profile_pic/', views.update_profile_pic, name='update_profile_pic'),
    path('remove-profile-pic/', views.remove_profile_pic, name='remove_profile_pic'),
    # Update this line to match the URL being requested
    path('zone_dashboard/', views.zone_dashboard, name='zone_dashboard'),
    path('cell-dashboard/', views.cell_dashboard, name='cell_dashboard'),
    path('zone/<int:zone_id>/', views.zone_detail, name='zone_detail'),  # Add this line
    path('cell-profile/', views.cell_profile, name='cell_profile'),  # Add this line
    # Remove or comment out this line:
    # Remove this line
    path('cell-monitoring/', views.cell_monitoring_view, name='cell_monitoring'),
    
    # Keep only this line for cells
    path('cells/', views.cells_view, name='cells'),
    path('cells/create/', views.create_cell, name='create_cell'),
    path('cells/edit/<int:cell_id>/', views.edit_cell, name='edit_cell'),
    path('cells/delete/<int:cell_id>/', views.delete_cell, name='delete_cell'),
    path('profile/', views.profile_view, name='profile_view'),  # Add this line
    path('create-issue/', views.create_issue, name='create_issue'),
    path('api/cell-issues/<int:issue_id>/delete/', views.delete_issue, name='delete_issue'),
    path('cell/assets/', views.cell_assets, name='cell_assets'),
    path('cell/assets/<int:asset_id>/delete/', views.delete_asset, name='delete_asset'),
    path('cell/assets/<int:asset_id>/edit/', views.edit_asset, name='edit_asset'),
    path('zone/assets/', views.zone_assets, name='zone_assets'),
    path('admin-assets/<int:zone_id>/', views.zone_assets_detail, name='admin_asset_details'),
    path('asset-admin/', views.asset_admin, name='asset_admin'),
    # Change these lines
    path('cell/assets/download-sample/', views.download_sample_csv, name='download_sample_csv'),
    # To these lines
    path('red-tag/', views.red_tag_view, name='red_tag'),
    path('api/red-tag/<int:item_id>/', views.red_tag_details, name='red_tag_details'),
    path('api/issues/<int:issue_id>/red-tag/', views.create_red_tag, name='create_red_tag'),
    path('red-tag-admin/', views.admin_red_tags, name='admin_red_tags'),
    path('red-tag-admin/zone/<int:zone_id>/', views.zone_red_tags, name='zone_red_tags'),
    path('api/issues/upload-after-image/', views.upload_after_image, name='upload_after_image'),
    path('api/zone-issues/<int:pk>/delete/', views.delete_zone_issue, name='delete_zone_issue'),
    # Add this line with your other asset-related URLs
    path('cell/assets/bulk-upload/', views.bulk_upload_assets, name='bulk_upload_assets'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/centers/', views.center_api, name='center_api'),
    path('api/centers/<int:center_id>/', views.center_detail_api, name='center_detail_api'),
    path('api/admins/', views.admin_api, name='admin_api'),
    path('api/admins/<int:admin_id>/', views.admin_detail_api, name='admin_detail_api'),
    path('centers/', views.centers_view, name='centers'),
    path('admins/', views.admins_view, name='admins'),
]