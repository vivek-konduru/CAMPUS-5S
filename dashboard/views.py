from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError  # Add this import
from .models import Zone, Cell, UserProfile, Issue, Comment, Asset, RedTag, Center  # Add Asset to the imports
from django.http import JsonResponse # type: ignore
from django.shortcuts import redirect # type: ignore
from django.contrib.auth import logout # type: ignore
from django.views.decorators.http import require_POST, require_http_methods # Add this import
from django.core.paginator import Paginator # type: ignore
from django.db.models import Q, Prefetch # type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test # type: ignore
from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.db.models import Count, Sum, F # type: ignore
from .models import Zone, Cell
from django.contrib.auth import authenticate, login # type: ignore
from django.contrib import messages  # Add this import at the top # type: ignore
from functools import wraps
from django.utils import timezone # type: ignore
from django.utils.timezone import localtime # type: ignore
from django.conf import settings # type: ignore
import json  # Add this at the top with other imports
import csv
import io
from django.http import HttpResponse # type: ignore
from django.core.exceptions import PermissionDenied # type: ignore
from dashboard.models import UserProfile # type: ignore


# Helper for superuser check
from django.contrib.auth.decorators import user_passes_test

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.userprofile.role != role:
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def is_zone_leader(user):
    return user.userprofile.role == 'zone_leader'

@login_required
@role_required('zone_leader')
def zone_dashboard(request):
    zone = request.user.userprofile.zone
    cells = Cell.objects.filter(zone=zone)
    total_cells = cells.count()
    cell_leaders = UserProfile.objects.filter(
        cell__zone=zone,
        role='cell_leader'
    )
    total_cell_leaders = cell_leaders.count()
    total_issues = Issue.objects.filter(cell__zone=zone).count()
    pending_issues = Issue.objects.filter(cell__zone=zone, status='pending').count()
    approved_issues = Issue.objects.filter(cell__zone=zone, status='approved').count()
    rejected_issues = Issue.objects.filter(cell__zone=zone, status='rejected').count()
    pending_percentage = round((pending_issues / total_issues * 100) if total_issues > 0 else 0)
    approved_percentage = round((approved_issues / total_issues * 100) if total_issues > 0 else 0)
    rejected_percentage = round((rejected_issues / total_issues * 100) if total_issues > 0 else 0)
    
    context = {
        'total_cells': total_cells,
        'total_cell_leaders': total_cell_leaders,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'pending_percentage': pending_percentage,
        'approved_percentage': approved_percentage,
        'rejected_percentage': rejected_percentage,
    }
    
    return render(request, 'dashboard/zone_dashboard.html', context)
    if not request.user.userprofile.role == 'zone_leader':
        return redirect('home')
        
    user = request.user
    zones = Zone.objects.filter(
        userprofile__user=user,
        userprofile__role='zone_leader'
    ).distinct()
    
    total_cells = Cell.objects.filter(zone__in=zones).count()
    total_cell_leaders = User.objects.filter(
        userprofile__role='cell_leader',
        userprofile__cell__zone__in=zones
    ).count()
    total_members = User.objects.filter(
        userprofile__cell__zone__in=zones
    ).count()

    context = {
        'zones': zones,
        'total_cells': total_cells,
        'total_cell_leaders': total_cell_leaders,
        'total_members': total_members,
    }
    return render(request, 'dashboard/zone_dashboard.html', context)

def landing(request):
    return render(request, 'dashboard/landing.html')

@login_required
def home(request):
    user_profile = request.user.userprofile
    
    # Filter counts by center for admin users
    if user_profile.role == 'admin':
        # Get data only for the admin's center
        if user_profile.center:
            users_count = User.objects.filter(userprofile__center=user_profile.center).count()
            zones_count = Zone.objects.filter(center=user_profile.center).distinct().count()
            cells_count = Cell.objects.filter(zone__center=user_profile.center).distinct().count()
            # Filter issues by center using zone.center, not userprofile
            issues = Issue.objects.filter(cell__zone__center=user_profile.center)
        else:
            # If admin has no center assigned, show no data
            users_count = 0
            zones_count = 0
            cells_count = 0
            issues = Issue.objects.none()
    else:
        # For non-admin users, show only data they have access to
        if user_profile.zone:
            users_count = User.objects.filter(userprofile__zone=user_profile.zone).count()
            zones_count = 1  # They can only see their own zone
            cells_count = Cell.objects.filter(zone=user_profile.zone).count()
            issues = Issue.objects.filter(cell__zone=user_profile.zone)
        elif user_profile.cell:
            users_count = User.objects.filter(userprofile__cell=user_profile.cell).count()
            zones_count = 1
            cells_count = 1
            issues = Issue.objects.filter(cell=user_profile.cell)
        else:
            users_count = 0
            zones_count = 0
            cells_count = 0
            issues = Issue.objects.none()
    
    # Calculate issue statistics
    total_issues = issues.count()
    pending_issues = issues.filter(status='pending').count()
    approved_issues = issues.filter(status='approved').count()
    rejected_issues = issues.filter(status='rejected').count()

    # Calculate percentages
    pending_percentage = round((pending_issues / total_issues * 100) if total_issues > 0 else 0)
    approved_percentage = round((approved_issues / total_issues * 100) if total_issues > 0 else 0)
    rejected_percentage = round((rejected_issues / total_issues * 100) if total_issues > 0 else 0)
    
    context = {
        'users_count': users_count,
        'zones_count': zones_count,
        'cells_count': cells_count,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'pending_percentage': pending_percentage,
        'approved_percentage': approved_percentage,
        'rejected_percentage': rejected_percentage,
    }
    return render(request, 'dashboard/home.html', context)

@login_required
def users(request):
    user_profile = request.user.userprofile
    users_list = User.objects.select_related(
        'userprofile',
        'userprofile__zone',
        'userprofile__cell',
        'userprofile__cell__zone'
    ).all()
    # Filter by center for admin users
    if user_profile.role == 'admin' and user_profile.center:
        users_list = users_list.filter(userprofile__center=user_profile.center)
    search_query = request.GET.get('search', '')
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    # Filter available users by center for dropdowns
    available_zone_leaders = User.objects.filter(
        userprofile__role='zone_leader',
        userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
    )
    available_cell_leaders = User.objects.filter(
        userprofile__role='cell_leader',
        userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
    )
    
    context = {
        'users': users,
        'search_query': search_query,
        'zones': Zone.objects.filter(userprofile__center=user_profile.center).distinct() if user_profile.role == 'admin' and user_profile.center else Zone.objects.all(),
        'total_users': users_list.count(),
        'admin_count': UserProfile.objects.filter(role='admin', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='admin').count(),
        'zone_leader_count': UserProfile.objects.filter(role='zone_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='zone_leader').count(),
        'cell_leader_count': UserProfile.objects.filter(role='cell_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='cell_leader').count(),
        'available_zone_leaders': available_zone_leaders,
        'available_cell_leaders': available_cell_leaders,
    }
    return render(request, 'dashboard/users.html', context)

@login_required
def create_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        center_id = request.POST.get('center')
        user_profile = request.user.userprofile

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            # Prepare context for re-rendering the user creation form
            zones = Zone.objects.filter(userprofile__center=user_profile.center).distinct() if user_profile.role == 'admin' and user_profile.center else Zone.objects.all()
            available_zone_leaders = User.objects.filter(
                userprofile__role='zone_leader',
                userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
            )
            available_cell_leaders = User.objects.filter(
                userprofile__role='cell_leader',
                userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
            )
            users_list = User.objects.select_related(
                'userprofile',
                'userprofile__zone',
                'userprofile__cell',
                'userprofile__cell__zone'
            ).all()
            if user_profile.role == 'admin' and user_profile.center:
                users_list = users_list.filter(userprofile__center=user_profile.center)
            paginator = Paginator(users_list, 10)
            page_number = request.GET.get('page')
            users = paginator.get_page(page_number)
            context = {
                'users': users,
                'search_query': request.GET.get('search', ''),
                'zones': zones,
                'total_users': users_list.count(),
                'admin_count': UserProfile.objects.filter(role='admin', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='admin').count(),
                'zone_leader_count': UserProfile.objects.filter(role='zone_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='zone_leader').count(),
                'cell_leader_count': UserProfile.objects.filter(role='cell_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='cell_leader').count(),
                'available_zone_leaders': available_zone_leaders,
                'available_cell_leaders': available_cell_leaders,
            }
            return render(request, 'dashboard/users.html', context)

        try:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.userprofile.role = role

            # Set zone directly if zone_id is provided
            zone_id = request.POST.get('zone')
            if zone_id:
                if role == 'zone_leader':
                    UserProfile.objects.filter(zone_id=zone_id, role='zone_leader').update(zone=None)
                    user.userprofile.zone_id = zone_id
                elif role == 'cell_leader':
                    # For cell leaders, assign the zone even without a cell
                    user.userprofile.zone_id = zone_id
                    
                    # If cell_id is provided, assign it too
                    cell_id = request.POST.get('cell')
                    if cell_id:
                        UserProfile.objects.filter(cell_id=cell_id, role='cell_leader').update(cell=None)
                        user.userprofile.cell_id = cell_id

            # Inherit center from admin
            if request.user.userprofile.role == 'admin' and request.user.userprofile.center:
                user.userprofile.center = request.user.userprofile.center

            user.userprofile.save()
            messages.success(request, "User created successfully.")
            return redirect('users')

        except IntegrityError:
            messages.error(request, "Username already exists.")
            # Same as above: re-render the form with context
            zones = Zone.objects.filter(userprofile__center=user_profile.center).distinct() if user_profile.role == 'admin' and user_profile.center else Zone.objects.all()
            available_zone_leaders = User.objects.filter(
                userprofile__role='zone_leader',
                userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
            )
            available_cell_leaders = User.objects.filter(
                userprofile__role='cell_leader',
                userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
            )
            users_list = User.objects.select_related(
                'userprofile',
                'userprofile__zone',
                'userprofile__cell',
                'userprofile__cell__zone'
            ).all()
            if user_profile.role == 'admin' and user_profile.center:
                users_list = users_list.filter(userprofile__center=user_profile.center)
            paginator = Paginator(users_list, 10)
            page_number = request.GET.get('page')
            users = paginator.get_page(page_number)
            context = {
                'users': users,
                'search_query': request.GET.get('search', ''),
                'zones': zones,
                'total_users': users_list.count(),
                'admin_count': UserProfile.objects.filter(role='admin', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='admin').count(),
                'zone_leader_count': UserProfile.objects.filter(role='zone_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='zone_leader').count(),
                'cell_leader_count': UserProfile.objects.filter(role='cell_leader', center=user_profile.center if user_profile.role == 'admin' else None).count() if user_profile.role == 'admin' else UserProfile.objects.filter(role='cell_leader').count(),
                'available_zone_leaders': available_zone_leaders,
                'available_cell_leaders': available_cell_leaders,
            }
            return render(request, 'dashboard/users.html', context)

    return redirect('users')

@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # For AJAX requests to get zone data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {}
        user_profile = request.user.userprofile
        
        # Get zones based on center
        if user_profile.role == 'admin' and user_profile.center:
            zones = Zone.objects.filter(center=user_profile.center)
        else:
            zones = Zone.objects.all()
        
        data['zones'] = list(zones.values('id', 'name'))
        
        # Also get cells for the zone if user is cell leader
        if user.userprofile.role == 'cell_leader' and user.userprofile.zone:
            cells = Cell.objects.filter(zone=user.userprofile.zone).values('id', 'name')
            data['cells'] = list(cells)
            
        return JsonResponse(data)

    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        new_role = request.POST['role']
        zone_id = request.POST.get('zone')
        user_profile = user.userprofile

        # Store old values for comparison
        old_role = user_profile.role
        old_zone = user_profile.zone
        old_cell = user_profile.cell

        # Update role
        user_profile.role = new_role
        
        # Handle zone and cell assignments
        if new_role in ['zone_leader', 'cell_leader']:
            if zone_id:
                new_zone = Zone.objects.get(id=zone_id)
                
                # For zone leaders, clear any previous leader of this zone
                if new_role == 'zone_leader':
                    UserProfile.objects.filter(
                        zone=new_zone,
                        role='zone_leader'
                    ).exclude(user=user).update(zone=None)
                    user_profile.cell = None
                    user_profile.zone = new_zone

                # For cell leaders
                elif new_role == 'cell_leader':
                    user_profile.zone = new_zone
                    cell_id = request.POST.get('cell')
                    if cell_id:
                        # Clear any previous leader of this cell
                        UserProfile.objects.filter(
                            cell_id=cell_id,
                            role='cell_leader'
                        ).exclude(user=user).update(cell=None)
                        user_profile.cell_id = cell_id
                    else:
                        user_profile.cell = None
            else:
                user_profile.zone = None
                user_profile.cell = None
        else:
            # For other roles, clear zone and cell
            user_profile.zone = None
            user_profile.cell = None

        # Handle admin status
        if new_role == 'admin':
            user.is_staff = True
        else:
            user.is_staff = False
        
        user.save()
        user_profile.save()

        messages.success(request, 'User updated successfully.')
        return redirect('users')

    # For AJAX requests to get zone data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_profile = request.user.userprofile
        data = {}
        
        # Get zones based on center
        if user_profile.role == 'admin' and user_profile.center:
            zones = Zone.objects.filter(center=user_profile.center)
        else:
            zones = Zone.objects.all()
            
        data['zones'] = list(zones.values('id', 'name'))
        
        # If user is cell leader, also get the cells for their zone
        zone_id = user.userprofile.zone_id
        if zone_id:
            cells = Cell.objects.filter(zone_id=zone_id).values('id', 'name')
            data['cells'] = list(cells)
            
        return JsonResponse(data)

    return redirect('users')

@login_required
@require_POST
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'status': 'success'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def get_zone_cells(request, zone_id):
    cells = Cell.objects.filter(zone_id=zone_id).values('id', 'name')
    return JsonResponse(list(cells), safe=False)

@login_required
def zones(request):
    user_profile = request.user.userprofile
    # Show only zones for the admin's center if admin, otherwise show all zones
    if user_profile.role == 'admin' and user_profile.center:
        zones_list = Zone.objects.filter(center=user_profile.center)
    else:
        zones_list = Zone.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        zones_list = zones_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        
    # Filter available users by center
    available_users = User.objects.filter(
        userprofile__role='zone_leader',
        userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
    )
    for zone in zones_list:
        zone.leader = UserProfile.objects.filter(zone=zone, role='zone_leader').select_related('user').first()
    context = {
        'zones': zones_list,
        'available_users': available_users,
        'total_zones': zones_list.count(),
        'total_cells': Cell.objects.filter(zone__in=zones_list).count(),
        'search_query': search_query,
    }
    return render(request, 'dashboard/zones.html', context)

@login_required
def create_zone(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        zone_leader_id = request.POST.get('zone_leader')
        user_profile = request.user.userprofile

        # Create zone with center if admin is creating
        zone = Zone.objects.create(
            name=name,
            description=description,
            center=user_profile.center if user_profile.role == 'admin' else None
        )

        # Only assign zone leader if one is selected (not empty)
        if zone_leader_id:
            leader_profile = UserProfile.objects.filter(user_id=zone_leader_id, role='zone_leader').first()
            if leader_profile:
                leader_profile.zone = zone
                if user_profile.role == 'admin' and user_profile.center:
                    leader_profile.center = user_profile.center
                leader_profile.save()

        return redirect('zones')
    return redirect('zones')

@login_required
def edit_zone(request, zone_id):
    if request.method == 'POST':
        zone = Zone.objects.get(id=zone_id)
        zone.name = request.POST['name']
        zone.description = request.POST.get('description', '')
        
        # Update zone leader
        new_leader_id = request.POST.get('zone_leader')
        if new_leader_id:
            # Remove previous zone leader
            UserProfile.objects.filter(zone=zone, role='zone_leader').update(zone=None)
            # Set new zone leader
            UserProfile.objects.filter(user_id=new_leader_id, role='zone_leader').update(zone=zone)
        
        zone.save()
        return redirect('zones')
    return redirect('zones')

@login_required
@require_POST
def delete_zone(request, zone_id):
    try:
        zone = Zone.objects.get(id=zone_id)
        zone.delete()
        return JsonResponse({'status': 'success'})
    except Zone.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Zone not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def logout_view(request):
    logout(request)
    return redirect('landing')  # Make sure 'landing' is the name of your landing page URL pattern

@login_required
def cells_view(request):
    user_profile = request.user.userprofile
    cells = Cell.objects.select_related('zone').all()
    
    # Filter by center for admin users and get zones
    if user_profile.role == 'admin' and user_profile.center:
        cells = cells.filter(zone__center=user_profile.center).distinct()
        zones = Zone.objects.filter(center=user_profile.center).distinct()
    else:
        zones = Zone.objects.all()

    # Debug print
    print(f"Total zones found: {zones.count()}")
    for zone in zones:
        print(f"Zone: {zone.name} (ID: {zone.id})")
    
    for cell in cells:
        cell.zone.leader = UserProfile.objects.filter(
            zone=cell.zone, 
            role='zone_leader'
        ).select_related('user').first()
        cell.leader = UserProfile.objects.filter(
            cell=cell, 
            role='cell_leader'
        ).select_related('user').first()
    search_query = request.GET.get('search', '')
    if search_query:
        cells = cells.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(zone__name__icontains=search_query)
        )
    # Only show zones for this center
    zones = Zone.objects.all()
    if user_profile.role == 'admin' and user_profile.center:
        zones = zones.filter(userprofile__center=user_profile.center).distinct()
        
    # Filter available leaders by center
    available_leaders = User.objects.filter(
        userprofile__role='cell_leader',
        userprofile__center=user_profile.center if user_profile.role == 'admin' and user_profile.center else F('userprofile__center')
    )
    
    total_cells = cells.count()
    context = {
        'cells': cells,
        'zones': zones,  # Make sure this is explicitly added
        'total_cells': total_cells,
        'search_query': search_query,
        'available_leaders': available_leaders,
        'debug_zones': list(zones.values('id', 'name'))  # Add this for debugging
    }
    return render(request, 'dashboard/cells.html', context)

@login_required
def create_cell(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST.get('description', '')
        zone_id = request.POST.get('zone')
        cell_leader_id = request.POST.get('cell_leader')
        
        cell = Cell.objects.create(
            name=name,
            description=description,
            zone_id=zone_id
        )
        
        if cell_leader_id:
            UserProfile.objects.filter(user_id=cell_leader_id, role='cell_leader').update(cell=cell)
            
        return redirect('cells')
    return redirect('cells')

@login_required
def edit_cell(request, cell_id):
    if request.method == 'POST':
        cell = Cell.objects.get(id=cell_id)
        cell.name = request.POST['name']
        cell.description = request.POST.get('description', '')
        cell.zone_id = request.POST.get('zone')
        
        # Update cell leader
        new_leader_id = request.POST.get('cell_leader')
        if new_leader_id:
            # Remove previous cell leader
            UserProfile.objects.filter(cell=cell, role='cell_leader').update(cell=None)
            # Set new cell leader
            UserProfile.objects.filter(user_id=new_leader_id, role='cell_leader').update(cell=cell)
        
        cell.save()
        return redirect('cells')
    return redirect('cells')

@login_required
@require_POST
def delete_cell(request, cell_id):
    try:
        cell = Cell.objects.get(id=cell_id)
        cell.delete()
        return JsonResponse({'status': 'success'})
    except Cell.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cell not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def issues(request):
    user_profile = request.user.userprofile

    # First, get the base queryset based on user role and center
    if user_profile.role == 'admin':
        if user_profile.center:
            # Use zone.center instead of userprofile__center
            base_queryset = Issue.objects.filter(cell__zone__center=user_profile.center)
        else:
            base_queryset = Issue.objects.none()
    elif user_profile.role == 'zone_leader':
        zone = user_profile.zone
        base_queryset = Issue.objects.filter(cell__zone=zone)
    else:
        cell = user_profile.cell
        base_queryset = Issue.objects.filter(cell=cell)

    # Apply select_related and prefetch_related for better performance
    issues = base_queryset.select_related(
        'cell',
        'cell__zone',
        'created_by',
        'asset'
    ).prefetch_related(
        'comments'
    ).order_by('-created_at')

    # Count issues by status using the base_queryset
    total_issues = base_queryset.count()
    pending_issues = base_queryset.filter(status='pending').count()
    approved_issues = base_queryset.filter(status='approved').count()
    rejected_issues = base_queryset.filter(status='rejected').count()

    context = {
        'issues': issues,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'MEDIA_URL': django_settings.MEDIA_URL,
    }
    
    return render(request, 'dashboard/issues.html', context)

# Add near other API handlers
@login_required
@require_POST
def upload_after_image(request):
    try:
        issue_id = request.POST.get('issue_id')
        after_image = request.FILES.get('after_image')
        
        if not issue_id or not after_image:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Add debug logging
        print(f"Attempting upload for issue {issue_id} with file {after_image.name}")
            
        issue = Issue.objects.get(id=issue_id)
        
        # Enhanced permission check
        if not (request.user.is_staff or 
                issue.created_by == request.user or 
                request.user.userprofile.role in ['admin', 'zone_leader']):
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Validate file size (5MB limit)
        if after_image.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 5MB limit'}, status=400)
        
        # Save with error handling
        try:
            issue.after_image = after_image
            issue.save()
            print(f"Successfully saved after image for issue {issue_id}")
            return JsonResponse({'success': True})
        except Exception as save_error:
            print(f"Save error: {str(save_error)}")
            return JsonResponse({'success': False, 'error': 'File save failed'}, status=500)
            
    except Issue.DoesNotExist:
        print(f"Issue not found: {issue_id}")
        return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Server error'}, status=500)

def delete_zone_issue(request, pk):
    if request.method == 'POST':
        try:
            # Change from ZoneIssue to Issue
            issue = Issue.objects.get(pk=pk)
            
            # Add permission check
            if not (request.user.is_staff or 
                    request.user.userprofile.role in ['admin', 'zone_leader']):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            # Optional: Verify zone ownership
            if request.user.userprofile.role == 'zone_leader':
                if issue.cell.zone != request.user.userprofile.zone:
                    return JsonResponse({'success': False, 'error': 'Not your zone issue'}, status=403)
            
            issue.delete()
            return JsonResponse({'success': True})
        except Issue.DoesNotExist:  # Changed exception type
            return JsonResponse({'success': False, 'error': 'Issue not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)


@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.save()
        return redirect('settings')
    return redirect('settings')

@login_required
def change_password(request):
    if request.method == 'POST':
        user = request.user
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if user.check_password(current_password) and new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            return redirect('login')
    return redirect('settings')

@login_required
def profile_view(request):
    user_profile = request.user.userprofile
    
    # Get zone-specific statistics if user is a zone leader
    if user_profile.role == 'zone_leader' and user_profile.zone:
        total_cells = Cell.objects.filter(zone=user_profile.zone).count()
        total_cell_leaders = UserProfile.objects.filter(
            cell__zone=user_profile.zone,
            role='cell_leader'
        ).count()
        total_issues = Issue.objects.filter(cell__zone=user_profile.zone).count()
    else:
        total_cells = 0
        total_cell_leaders = 0
        total_issues = 0

    context = {
        'user': request.user,
        'profile': user_profile,
        'total_cells': total_cells,
        'total_cell_leaders': total_cell_leaders,
        'total_issues': total_issues,
    }
    return render(request, 'dashboard/profile.html', context)

@login_required
def user_settings(request):
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/settings.html', context)

def asset_admin(request):
    user_profile = request.user.userprofile
    
    # Filter zones by center for admin users
    if user_profile.role == 'admin' and user_profile.center:
        zones = Zone.objects.filter(userprofile__center=user_profile.center).distinct()
    else:
        zones = Zone.objects.none()
        
    for zone in zones:
        # Add total assets count
        zone.total_assets = Asset.objects.filter(cell__zone=zone).count()
        
        # Add total cells count
        zone.total_cells = Cell.objects.filter(zone=zone).count()

        # Get asset types distribution
        zone.asset_types = Asset.objects.filter(cell__zone=zone).values('asset_type').annotate(
            count=Count('asset_type'),
            type=F('asset_type')
        )
        
        # Get recent assets
        zone.recent_assets = Asset.objects.filter(cell__zone=zone).order_by('-added_date')[:3]
        
        # Get total issues
        zone.total_issues = Issue.objects.filter(cell__zone=zone).count()

    return render(request, 'dashboard/asset_admin.html', {'zones': zones})

@login_required
def remove_profile_pic(request):
    if request.method == 'POST':
        user_profile = request.user.userprofile
        user_profile.profile_pic = None
        user_profile.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        profile_pic = request.FILES['profile_pic']
        user_profile = request.user.userprofile
        user_profile.profile_pic = profile_pic
        user_profile.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Only superusers can access admin_dashboard
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.userprofile.role == 'zone_leader':
                return redirect('zone_dashboard')
            elif user.userprofile.role == 'cell_leader':
                return redirect('cell_dashboard')
            elif user.userprofile.role == 'admin':
                return redirect('home')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'registration/login.html')  # Updated template path


@login_required
@user_passes_test(is_zone_leader)
def zone_detail(request, zone_id):
    zone = Zone.objects.get(id=zone_id)
    
    # Get all cells in this zone
    cells = Cell.objects.filter(zone=zone)
    
    # Get cell leaders count
    cell_leaders_count = UserProfile.objects.filter(
        cell__zone=zone,
        role='cell_leader'
    ).count()
    
    # Get total members count
    total_members = UserProfile.objects.filter(
        cell__zone=zone
    ).count()
    
    context = {
        'zone': zone,
        'cells': cells,
        'cell_leaders_count': cell_leaders_count,
        'total_members': total_members,
    }
    return render(request, 'dashboard/zone_detail.html', context)


@login_required
@role_required('zone_leader')
def zone_dashboard(request):
    zone = request.user.userprofile.zone
    cells = Cell.objects.filter(zone=zone)
    total_cells = cells.count()
    cell_leaders = UserProfile.objects.filter(
        cell__zone=zone,
        role='cell_leader'
    )
    total_cell_leaders = cell_leaders.count()
    total_issues = Issue.objects.filter(cell__zone=zone).count()
    pending_issues = Issue.objects.filter(cell__zone=zone, status='pending').count()
    approved_issues = Issue.objects.filter(cell__zone=zone, status='approved').count()
    rejected_issues = Issue.objects.filter(cell__zone=zone, status='rejected').count()
    pending_percentage = round((pending_issues / total_issues * 100) if total_issues > 0 else 0)
    approved_percentage = round((approved_issues / total_issues * 100) if total_issues > 0 else 0)
    rejected_percentage = round((rejected_issues / total_issues * 100) if total_issues > 0 else 0)
    
    context = {
        'total_cells': total_cells,
        'total_cell_leaders': total_cell_leaders,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'pending_percentage': pending_percentage,
        'approved_percentage': approved_percentage,
        'rejected_percentage': rejected_percentage,
    }
    
    return render(request, 'dashboard/zone_dashboard.html', context)

@login_required
@role_required('zone_leader')
def zone_assets(request):
    zone = request.user.userprofile.zone
    cell_id = request.GET.get('cell_id')
    
    if cell_id:
        # Detailed view for a specific cell
        cell = Cell.objects.get(id=cell_id, zone=zone)
        assets = Asset.objects.filter(cell=cell).order_by('-added_date')
        
        # Calculate statistics for the cell
        total_assets = assets.count()
        assets_by_type = assets.values('asset_type').annotate(count=Count('id'))
        
        context = {
            'cell': cell,
            'assets': assets,
            'total_assets': total_assets,
            'assets_by_type': assets_by_type,
            'is_detail_view': True
        }
        return render(request, 'dashboard/zone_assets_detail.html', context)
    
    # Original overview of all cells
    cells = Cell.objects.filter(zone=zone)
    for cell in cells:
        cell.asset_types = Asset.objects.filter(cell=cell).values('asset_type').annotate(count=Count('id'))
        cell.recent_assets = Asset.objects.filter(cell=cell).order_by('-added_date')[:3]
        total_assets = Asset.objects.filter(cell=cell).count()
        assets_with_issues = Asset.objects.filter(cell=cell, issues__isnull=False).distinct().count()
        cell.asset_usage_rate = (assets_with_issues / total_assets * 100) if total_assets > 0 else 0
        cell.asset_issues_count = Issue.objects.filter(cell=cell, asset__isnull=False).count()
    
    context = {
        'cells': cells,
        'is_detail_view': False
    }
    return render(request, 'dashboard/zone_assets.html', context)


@login_required
def zone_assets_detail(request, zone_id):
    zone = Zone.objects.get(id=zone_id)
    assets = Asset.objects.filter(cell__zone=zone).select_related('cell')
    
    cells = Cell.objects.filter(zone=zone).prefetch_related('assets')
    
    context = {
        'zone': zone,
        'cells': cells,
        'total_assets': assets.count(),
        'asset_types': Asset.objects.filter(cell__zone=zone).values('asset_type').annotate(
            count=Count('asset_type'),
            type=F('asset_type')
        )
    }
    return render(request, 'dashboard/admin_asset_details.html', context)

@login_required
def red_tag_view(request):
    # Get red tag items for the zone leader's zone
    red_tag_items = RedTag.objects.filter(
        asset__cell__zone=request.user.userprofile.zone
    ).select_related('asset', 'issue').order_by('-created_at')
    
    context = {
        'red_tag_items': red_tag_items,
        'red_tag_count': red_tag_items.count(),
    }
    return render(request, 'dashboard/red_tag.html', context)

@login_required
def red_tag_details(request, item_id):
    try:
        red_tag = RedTag.objects.select_related('asset', 'issue').get(id=item_id)
        
        # Check if asset exists
        if not red_tag.asset:
            return JsonResponse({'error': 'Asset not found for this red tag'}, status=404)
            
        response_data = {
            'asset': {
                'type': red_tag.asset.get_asset_type_display() if hasattr(red_tag.asset, 'get_asset_type_display') else str(red_tag.asset.asset_type),
                'id': red_tag.asset.asset_id
            },
            'issue': {
                'title': red_tag.issue.title,
                'description': red_tag.issue.description,
                'image': red_tag.issue.image.url if red_tag.issue.image else None
            },
            'damage_category': red_tag.get_damage_category_display() if hasattr(red_tag, 'get_damage_category_display') else str(red_tag.damage_category),
            'action_required': red_tag.get_action_required_display() if hasattr(red_tag, 'get_action_required_display') else str(red_tag.action_required),
            'notes': red_tag.notes or ''
        }
        
        return JsonResponse(response_data)
    except RedTag.DoesNotExist:
        return JsonResponse({'error': 'Red tag item not found'}, status=404)
    except Exception as e:
        print(f"Error in red_tag_details: {str(e)}")  # Add logging for debugging
        return JsonResponse({'error': 'An error occurred while fetching red tag details'}, status=500)

@login_required
@role_required('admin')
def admin_red_tags(request):
    # Only show zones from the admin's center
    if request.user.userprofile.center:
        # Get all zones for this center, ordered by id to preserve original order
        zones_qs = Zone.objects.filter(center=request.user.userprofile.center).order_by('id')
        # Only keep the zone with the most cells (the "original" one), skip zones with no cells
        zones = []
        for zone in zones_qs:
            # Only add zones that have at least one cell
            if Cell.objects.filter(zone=zone).exists():
                zones.append(zone)
        # If all zones have no cells, fallback to the first zone (to avoid empty page)
        if not zones and zones_qs.exists():
            zones = [zones_qs.first()]
    else:
        zones = []

    for zone in zones:
        # Get red tags for this zone
        zone_red_tags = RedTag.objects.filter(asset__cell__zone=zone)
        
        # Total red tags
        zone.total_red_tags = zone_red_tags.count()
        
        # Get damage categories
        zone.damage_categories = zone_red_tags.values('damage_category').annotate(
            name=F('damage_category'),
            count=Count('id')
        )
        
        # Recent red tags
        zone.recent_red_tags = zone_red_tags.select_related('asset').order_by('-created_at')[:3]
        
        # Statistics
        zone.pending_actions = zone_red_tags.filter(resolved=False).count()
        zone.resolved_items = zone_red_tags.filter(resolved=True).count()
    
    context = {
        'zones': zones
    }
    return render(request, 'dashboard/admin_red_tags.html', context)

@login_required
@role_required('admin')
def zone_red_tags(request, zone_id):
    # First verify the zone belongs to the admin's center
    if request.user.userprofile.center:
        zone = get_object_or_404(Zone, id=zone_id, center=request.user.userprofile.center)
    else:
        return HttpResponseForbidden("You don't have permission to view this zone")
    
    cells = Cell.objects.filter(zone=zone).prefetch_related(
        Prefetch(
            'assets',
            queryset=Asset.objects.prefetch_related('redtag_set')
        )
    ).annotate(
        red_tag_count=Count('assets__redtag')
    )

    total_red_tags = RedTag.objects.filter(asset__cell__zone=zone).count()

    context = {
        'zone': zone,
        'cells': cells,
        'total_red_tags': total_red_tags,
    }
    return render(request, 'dashboard/admin_red_tags_details.html', context)


@login_required
@require_POST
def create_red_tag(request, issue_id):
    try:
        # Get the issue and related asset
        issue = Issue.objects.get(id=issue_id)
        data = json.loads(request.body)
        
        # Create the red tag
        red_tag = RedTag.objects.create(
            issue=issue,
            asset=issue.asset,
            damage_category=data.get('category'),
            action_required=data.get('action'),
            notes=data.get('notes')
        )
        
        # Update issue status if not already approved
        if issue.status != 'approved':
            issue.status = 'approved'
            issue.save()
            
        return JsonResponse({'status': 'success', 'message': 'Red tag created successfully'})
        
    except Issue.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Issue not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@role_required('cell_leader')
def cell_dashboard(request):
    cell = request.user.userprofile.cell
    
    # Only count members who are actually assigned to this cell
    total_members = UserProfile.objects.filter(
        cell=cell,
        cell__isnull=False  # Make sure cell is actually assigned
    ).count()
    
    # Get issue statistics
    total_issues = Issue.objects.filter(cell=cell).count()
    pending_issues = Issue.objects.filter(cell=cell, status='pending').count()
    approved_issues = Issue.objects.filter(cell=cell, status='approved').count()
    rejected_issues = Issue.objects.filter(cell=cell, status='rejected').count()
    
    # Calculate percentages
    if total_issues > 0:
        pending_percentage = (pending_issues / total_issues) * 100
        approved_percentage = (approved_issues / total_issues) * 100
        rejected_percentage = (rejected_issues / total_issues) * 100
    else:
        pending_percentage = approved_percentage = rejected_percentage = 0
    
    context = {
        'total_members': total_members,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'pending_percentage': round(pending_percentage, 1),
        'approved_percentage': round(approved_percentage, 1),
        'rejected_percentage': round(rejected_percentage, 1),
    }
    
    return render(request, 'dashboard/cell_dashboard.html', context)

@login_required
@role_required('cell_leader')
def cell_members(request):
    # Get the current user's cell
    cell = request.user.userprofile.cell
    
    # Only get members specifically assigned to this cell
    members = UserProfile.objects.filter(
        cell=cell,  # Must be assigned to this cell
        cell__isnull=False  # Must have a cell assignment
    ).select_related('user')
    
    total_members = members.count()
    total_issues = Issue.objects.filter(cell=cell).count() if cell else 0

    context = {
        'members': members,
        'total_members': total_members,
        'total_issues': total_issues,
    }
    
    return render(request, 'dashboard/cell_members.html', context)
@login_required
@role_required('cell_leader')
def cell_issues(request):
    cell = request.user.userprofile.cell
    all_issues = Issue.objects.filter(cell=cell).prefetch_related('comments__user').order_by('-created_at')
    
    # Add pagination
    paginator = Paginator(all_issues, 5)  # Show 10 issues per page
    page_number = request.GET.get('page')
    issues = paginator.get_page(page_number)
    
    context = {
        'issues': issues,
        'total_issues': all_issues.count(),
        'pending_issues': all_issues.filter(status='pending').count(),
        'approved_issues': all_issues.filter(status='approved').count(),
        'rejected_issues': all_issues.filter(status='rejected').count(),
        'cell_assets': request.user.userprofile.cell.assets.all(),
    }
    return render(request, 'dashboard/cell_issues.html', context)

@login_required
def create_issue(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        asset_id = request.POST.get('asset')
        cell = request.user.userprofile.cell
        image = request.FILES.get('image')
        
        # Create the issue first
        issue = Issue.objects.create(
            title=title,
            description=description,
            priority=priority,
            cell=cell,
            created_by=request.user,
            status='pending'
        )
        
        # Associate the asset if provided
        if asset_id:
            try:
                asset = Asset.objects.get(id=asset_id, cell=cell)  # Ensure asset belongs to the cell
                issue.asset = asset
                issue.save()
            except Asset.DoesNotExist:
                print(f"Asset with ID {asset_id} not found")
        
        # Handle image if provided
        if image:
            issue.image = image
            issue.save()
        
        return redirect('cell_issues')
    return redirect('cell_issues')

@login_required
def cell_profile(request):
    cell = request.user.userprofile.cell
    total_members = UserProfile.objects.filter(cell=cell).count()
    total_issues = Issue.objects.filter(cell=cell).count()
    
    context = {
        'total_members': total_members,
        'total_issues': total_issues,
    }
    return render(request, 'dashboard/cell_profile.html', context)

@require_POST
def add_comment(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content')
        else:
            content = request.POST.get('content')
        
        if not content:
            return JsonResponse({'status': 'error', 'message': 'Content is required'}, status=400)

        # Create the comment
        comment = Comment.objects.create(
            issue=issue,
            user=request.user,
            content=content
        )
        
        return JsonResponse({
            'status': 'success',
            'comment': {
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%B %d, %Y %I:%M %p')
            }
        })
        
    except Issue.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Issue not found'}, status=404)
    except Exception as e:
        # Log the error for debugging
        import traceback
        print("Error in add_comment:", str(e))
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def issue_details(request, issue_id):
    try:
        issue = Issue.objects.select_related(
            'cell', 
            'cell__zone', 
            'created_by', 
            'asset'
        ).get(id=issue_id)
        
        # Debug print to check the data
        print(f"Priority: {issue.priority}")
        print(f"Asset: {issue.asset}")
        
        response_data = {
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'priority': issue.priority,
            'status': issue.status,
            'cell_name': issue.cell.name,
            'zone_name': issue.cell.zone.name,
            'created_by': issue.created_by.username,
            'created_at': issue.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'image': issue.image.url if issue.image else None,
        }

        # Add asset data if it exists
        if issue.asset:
            response_data['asset'] = {
                'type': issue.asset.get_asset_type_display(),
                'id': issue.asset.asset_id
            }
        
        # Add comments
        comments = issue.comments.select_related('user').order_by('-created_at')
        response_data['comments'] = [{
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for comment in comments]
        
        return JsonResponse(response_data)
    except Issue.DoesNotExist:
        return JsonResponse({'error': 'Issue not found'}, status=404)
    except Exception as e:
        print(f"Error in issue_details: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)


@login_required
def delete_cell_issue(request, issue_id):
    if request.method == 'POST':
        try:
            issue = Issue.objects.get(id=issue_id)
            issue.delete()
            return JsonResponse({'status': 'success'})
        except Issue.DoesNotExist:
            return JsonResponse({'error': 'Issue not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@require_POST
def approve_issue(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
        issue.status = 'approved'
        issue.save()
        return JsonResponse({'status': 'success'})
    except Issue.DoesNotExist:
        return JsonResponse({'error': 'Issue not found'}, status=404)

@require_POST
def reject_issue(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
        if request.user.userprofile.role in ['admin', 'zone_leader']:
            issue.status = 'rejected'
            issue.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
    except Issue.DoesNotExist:
        return JsonResponse({'error': 'Issue not found'}, status=404)

@login_required
@require_POST
def delete_issue(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
        issue.delete()
        return JsonResponse({'status': 'success'})
    except Issue.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Issue not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@role_required('zone_leader')
def cell_monitoring_view(request):
    # Get cells for the zone leader's zone
    user_profile = request.user.userprofile
    if user_profile.role == 'zone_leader' and user_profile.zone:
        cells = Cell.objects.filter(zone=user_profile.zone)
        for cell in cells:
            cell.leader = cell.get_active_leader()
            cell.active_members = UserProfile.objects.filter(cell=cell).count()
            cell.recent_issues = Issue.objects.filter(cell=cell).order_by('-created_at')[:3]
            total_issues = Issue.objects.filter(cell=cell).count()
            resolved_issues = Issue.objects.filter(cell=cell, status='approved').count()
            cell.resolution_rate = (resolved_issues / total_issues * 100) if total_issues > 0 else 0
            cell.total_issues = total_issues
            
    else:
        cells = []

    context = {
        'cells': cells,
    }
    return render(request, 'dashboard/cell_monitoring.html', context)

@login_required
def zone_issues_view(request):
    if not request.user.userprofile.role == 'zone_leader':
        return redirect('home')
    zone = request.user.userprofile.zone
    issues = Issue.objects.filter(cell__zone=zone)
    # Get statistics
    total_issues = issues.count()
    pending_issues = issues.filter(status='pending').count()
    approved_issues = issues.filter(status='approved').count()
    rejected_issues = issues.filter(status='rejected').count()
    # Get cells for filtering
    cells = Cell.objects.filter(zone=zone)
    context = {
        'issues': issues,
        'total_issues': total_issues,
        'pending_issues': pending_issues,
        'approved_issues': approved_issues,
        'rejected_issues': rejected_issues,
        'cells': cells,
    }
    
    return render(request, 'dashboard/zone_issues.html', context)


@login_required
@role_required('cell_leader')
def cell_assets(request):
    if request.method == 'POST':
        asset_type = request.POST.get('asset_type')
        asset_id = request.POST.get('asset_id')
        
        print(f"Received POST data - Type: {asset_type}, ID: {asset_id}")  # Debug print
        
        try:
            # Check if combination exists
            existing = Asset.objects.filter(
                cell=request.user.userprofile.cell,
                asset_type=asset_type,
                asset_id=asset_id
            ).exists()
            
            if existing:
                messages.error(request, f'Asset {asset_type}-{asset_id} already exists in your cell!')
                return redirect('cell_assets')
            
            asset = Asset.objects.create(
                asset_type=asset_type,
                asset_id=asset_id,
                cell=request.user.userprofile.cell,
                added_by=request.user
            )
            print(f"Asset created successfully: {asset}")  # Debug print
            messages.success(request, 'Asset added successfully!')
            
        except Exception as e:
            print(f"Error creating asset: {str(e)}")  # Debug print
            messages.error(request, f'Error creating asset: {str(e)}')
            
        return redirect('cell_assets')
    
    assets = Asset.objects.filter(cell=request.user.userprofile.cell)
    
    # Calculate statistics
    total_assets = assets.count()
    assets_by_type = {}
    for type_value, type_label in Asset.ASSET_TYPE_CHOICES:
        count = assets.filter(asset_type=type_value).count()
        if count > 0:  # Only include types that have assets
            assets_by_type[type_label] = count

    assets_list = Asset.objects.filter(cell=request.user.userprofile.cell).order_by('-added_date')
    paginator = Paginator(assets_list, 10)  # Show 10 assets per page
    
    page_number = request.GET.get('page')
    assets = paginator.get_page(page_number)

    context = {
        'assets': assets,
        'asset_types': Asset.ASSET_TYPE_CHOICES,
        'total_assets': total_assets,
        'assets_by_type': assets_by_type,
    }
    return render(request, 'dashboard/cell_assets.html', context)


def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_assets.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['asset_type', 'asset_id'])
    writer.writerow(['bench', '1'])
    writer.writerow(['chair', '2'])
    writer.writerow(['light', '3'])
    writer.writerow(['table', '4'])
    writer.writerow(['fan', '5'])
    
    return response

def bulk_upload_assets(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'No file was uploaded.')
            return redirect('cell_assets')
            
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('cell_assets')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(io.StringIO(decoded_file))
            next(csv_data)  # Skip header row
            
            success_count = 0
            error_count = 0
            
            for row in csv_data:
                try:
                    if len(row) != 2:
                        continue
                        
                    asset_type, asset_id = row
                    
                    # Check if asset already exists
                    if not Asset.objects.filter(
                        cell=request.user.userprofile.cell,
                        asset_type=asset_type,
                        asset_id=asset_id
                    ).exists():
                        Asset.objects.create(
                            cell=request.user.userprofile.cell,
                            asset_type=asset_type,
                            asset_id=asset_id,
                            added_by=request.user
                        )
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    continue
            
            if success_count > 0:
                messages.success(request, f'Successfully added {success_count} assets.')
            if error_count > 0:
                messages.warning(request, f'Failed to add {error_count} assets (duplicates or invalid data).')
                
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            
        return redirect('cell_assets')
        
    return redirect('cell_assets')


@login_required
@require_POST
def delete_asset(request, asset_id):
    try:
        # Get the asset and verify it belongs to the user's cell
        asset = Asset.objects.get(
            id=asset_id,
            cell=request.user.userprofile.cell
        )
        asset.delete()
        messages.success(request, 'Asset deleted successfully!')
        return JsonResponse({'status': 'success'})
    except Asset.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Asset not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def edit_asset(request, asset_id):
    try:
        asset = Asset.objects.get(id=asset_id, cell=request.user.userprofile.cell)
        data = json.loads(request.body)
        
        # Check if new asset_id already exists for this type (excluding current asset)
        if Asset.objects.filter(
            cell=request.user.userprofile.cell,
            asset_type=data['asset_type'],
            asset_id=data['asset_id']
        ).exclude(id=asset_id).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Asset ID already exists for this type'
            }, status=400)
        
        asset.asset_type = data['asset_type']
        asset.asset_id = data['asset_id']
        asset.save()
        
        return JsonResponse({'status': 'success'})
    except Asset.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Asset not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    context = {
        'centers_count': Center.objects.count(),
        'admins_count': User.objects.filter(is_staff=True).count(),
        'active_users_count': User.objects.filter(is_active=True).count(),
        'centers': Center.objects.all(),
        'admins': User.objects.filter(is_staff=True),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "POST"])
def center_api(request):
    if request.method == "GET":
        centers = Center.objects.all()
        return JsonResponse([{
            'id': center.id,
            'name': center.name,
            'location': center.location,
            'description': center.description
        } for center in centers], safe=False)
    
    elif request.method == "POST":
        data = json.loads(request.body)
        center = Center.objects.create(
            name=data['name'],
            location=data['location'],
            description=data.get('description', '')
        )
        return JsonResponse({'id': center.id}, status=201)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def center_detail_api(request, center_id):
    try:
        center = Center.objects.get(id=center_id)
    except Center.DoesNotExist:
        return JsonResponse({'error': 'Center not found'}, status=404)

    if request.method == "GET":
        return JsonResponse({
            'id': center.id,
            'name': center.name,
            'location': center.location,
            'description': center.description
        })
    
    elif request.method == "PUT":
        data = json.loads(request.body)
        center.name = data['name']
        center.location = data['location']
        center.description = data.get('description', '')
        center.save()
        return JsonResponse({'status': 'success'})
    
    elif request.method == "DELETE":
        center.delete()
        return JsonResponse({'status': 'success'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "POST"])
def admin_api(request):
    if request.method == "GET":
        admins = User.objects.filter(is_staff=True)
        return JsonResponse([{
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'center_id': admin.userprofile.center.id if admin.userprofile.center else None
        } for admin in admins], safe=False)
    
    elif request.method == "POST":
        data = json.loads(request.body)
        admin = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            is_staff=True,
            is_superuser=False  # Ensure admin is NOT a superuser
        )
        center_id = data.get('center_id')
        if center_id:
            try:
                center = Center.objects.get(id=center_id)
                admin.userprofile.center = center
                admin.userprofile.save()
            except Center.DoesNotExist:
                return JsonResponse({'error': 'Center not found'}, status=400)
        else:
            admin.userprofile.center = None
            admin.userprofile.save()
        admin.userprofile.role = 'admin'
        admin.userprofile.save()
        return JsonResponse({'id': admin.id}, status=201)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "PUT", "DELETE"])
def admin_detail_api(request, admin_id):
    try:
        admin = User.objects.get(id=admin_id, is_staff=True)
        profile, created = UserProfile.objects.get_or_create(user=admin)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Admin not found'}, status=404)

    if request.method == "GET":
        return JsonResponse({
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'center_id': profile.center.id if profile.center else None
        })
    
    elif request.method == "PUT":
        data = json.loads(request.body)
        admin.username = data.get('username', admin.username)
        admin.email = data.get('email', admin.email)
        admin.save()
        
        center_id = data.get('center_id')
        if center_id:
            try:
                profile.center = Center.objects.get(id=center_id)
            except Center.DoesNotExist:
                return JsonResponse({'error': 'Center not found'}, status=400)
        else:
            profile.center = None
        profile.save()
        
        return JsonResponse({'status': 'success'})
    
    elif request.method == "DELETE":
        try:
            admin.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
@superuser_required
def centers_view(request):
    context = {
        'centers': Center.objects.all(),
    }
    return render(request, 'dashboard/centers.html', context)


@login_required
@superuser_required
def admins_view(request):
    context = {
        'admins': User.objects.filter(
            is_staff=True,
            userprofile__center__isnull=False
        ).distinct(),
        'centers': Center.objects.all(),
    }
    return render(request, 'dashboard/admins.html', context)

@login_required
def get_zones(request):
    """API endpoint to get zones for dropdowns"""
    user_profile = request.user.userprofile
    if user_profile.role == 'admin' and user_profile.center:
        zones = Zone.objects.filter(center=user_profile.center)
    else:
        zones = Zone.objects.all()
    return JsonResponse(list(zones.values('id', 'name')), safe=False)

