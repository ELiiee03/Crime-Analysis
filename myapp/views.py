from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
from collections import Counter
from .forms import (
    CSVUploadForm, LoginForm, CustomUserCreationForm,
    CustomUserEditForm, CustomPasswordChangeForm, CrimeDataForm
)
from .models import CrimeData, UserActivity
import json
from django.core.paginator import Paginator


# Utility Functions
def forbidden_access(request):
    """Render a forbidden access page for unauthorized users."""
    return render(request, '403.html', status=403)


def role_required(role):
    """Utility function for role-based access control."""

    def decorator(user):
        if role == 'admin':
            return user.is_superuser
        elif role == 'user':
            return not user.is_superuser
        return False

    return decorator


# Authentication Views
def login_view(request):
    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        return redirect('admin_dashboard' if request.user.is_superuser else 'user_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)

                # Log login activity
                log_activity(
                    user=user,
                    action_type='login',
                    description=f"{user.username} logged in",
                    request=request
                )

                # Set a session variable to handle browser back button
                request.session['is_logged_in'] = True

                # Set cache control headers to prevent caching of sensitive pages
                response = redirect('admin_dashboard' if user.is_superuser else 'user_dashboard')
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                messages.error(request, "Invalid credentials.")
        else:
            messages.error(request, "Form is invalid.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')


# Helper function to log user activities
def log_activity(user, action_type, description, records_affected=0, request=None):
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    UserActivity.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        records_affected=records_affected,
        ip_address=ip_address
    )


# Dashboard Views
@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def admin_dashboard(request):
    # Get total records and calculate change from last month
    current_month = timezone.now().month
    current_year = timezone.now().year

    # Handle previous month (accounting for year change)
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    # Get current and previous month records
    current_month_records = CrimeData.objects.filter(
        date_committed__month=current_month,
        date_committed__year=current_year
    ).count()

    prev_month_records = CrimeData.objects.filter(
        date_committed__month=prev_month,
        date_committed__year=prev_year
    ).count()

    # Calculate percentage change
    if prev_month_records > 0:
        records_percentage = round(((current_month_records - prev_month_records) / prev_month_records) * 100, 1)
    else:
        records_percentage = 0

    # Get active users and new users this week
    active_users = User.objects.filter(is_active=True).count()

    one_week_ago = timezone.now() - timedelta(days=7)
    new_users_this_week = User.objects.filter(
        date_joined__gte=one_week_ago,
        is_active=True
    ).count()

    # Get unique locations and change from last month
    current_month_cities = CrimeData.objects.filter(
        date_committed__month=current_month,
        date_committed__year=current_year
    ).values('city').distinct().count()

    prev_month_cities = CrimeData.objects.filter(
        date_committed__month=prev_month,
        date_committed__year=prev_year
    ).values('city').distinct().count()

    locations_change = current_month_cities - prev_month_cities

    # Get total crime records overall
    total_records = CrimeData.objects.count()

    # Get recent activities
    recent_activities = UserActivity.objects.all().order_by('-timestamp')[:10]

    # Get separate activities for users and admins - REMOVED THE LIMIT
    admin_activities = UserActivity.objects.filter(user__is_superuser=True).order_by('-timestamp')
    user_activities = UserActivity.objects.filter(user__is_superuser=False).order_by('-timestamp')

    # Get severity distribution
    high_severity_count = CrimeData.objects.filter(severity='High').count()
    medium_severity_count = CrimeData.objects.filter(severity='Medium').count()
    low_severity_count = CrimeData.objects.filter(severity='Low').count()

    context = {
        'total_records': total_records,
        'records_percentage': records_percentage,
        'active_users': active_users,
        'new_users_this_week': new_users_this_week,
        'unique_locations': CrimeData.objects.values('city').distinct().count(),
        'locations_change': locations_change,
        'recent_activities': recent_activities,
        'admin_activities': admin_activities,
        'user_activities': user_activities,
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'low_severity_count': low_severity_count,
    }

    return render(request, 'admin/admin_dashboard.html', context)


@login_required
@user_passes_test(role_required('user'), login_url='/forbidden/')
def user_dashboard(request):
    # Get severity distribution for user dashboard
    high_severity_count = CrimeData.objects.filter(severity='High').count()
    medium_severity_count = CrimeData.objects.filter(severity='Medium').count()
    low_severity_count = CrimeData.objects.filter(severity='Low').count()

    context = {
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'low_severity_count': low_severity_count,
    }

    return render(request, 'user/user_dashboard.html', context)


# Add this new function to determine severity based on crime frequency
def determine_severity_by_frequency(offense_type, count, city=None, barangay=None):
    """
    Determine severity based on crime frequency and offense type, with location context.

    Args:
        offense_type: Type of offense
        count: Number of occurrences
        city: Optional city parameter
        barangay: Optional barangay parameter

    Returns:
        String indicating severity level: 'High', 'Medium', or 'Low'
    """
    offense_type = offense_type.lower()

    # Define base severities for different offense types
    # You may need to adjust these based on your specific offense types
    violent_crimes = ['murder', 'homicide', 'physical injury', 'rape', 'robbery', 'carnapping']
    property_crimes = ['theft', 'burglary', 'shoplifting', 'vandalism']
    drug_crimes = ['drug', 'possession', 'trafficking']

    if any(crime in offense_type for crime in violent_crimes):
        base_severity = 'High'
    elif any(crime in offense_type for crime in property_crimes):
        base_severity = 'Medium'
    elif any(crime in offense_type for crime in drug_crimes):
        base_severity = 'Medium'
    else:
        base_severity = 'Low'  # Default for other crimes

    # Adjust severity based on frequency
    if count >= 100:
        # High frequency overrides base severity
        return 'High'
    elif count >= 50:
        # High frequency bumps up severity
        if base_severity == 'Low':
            return 'Medium'
        else:
            return 'High'  # Elevate to High if already Medium or High
    elif count >= 20:
        # Medium frequency bumps up severity slightly
        if base_severity == 'Low':
            return 'Medium'
        else:
            return base_severity  # Keep existing severity if already Medium or High
    else:
        # Low frequency, keep base severity
        return base_severity


# Update the upload_file function to use the new data structure
@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def upload_file(request):
    template = 'admin/upload.html'  # Only admin template is needed now

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                # Read the CSV file
                data = pd.read_csv(csv_file)

                # Check if the file has the expected number of columns
                if len(data.columns) < 7:
                    return HttpResponse(
                        "CSV file must have at least 7 columns for police office, barangay, date, time, offense, latitude, and longitude.",
                        status=400)

                # Rename columns to match expected names
                # The first column is the police office which contains city information
                # The second column (Unnamed: 1) is the barangay
                # And so on...
                column_mapping = {
                    data.columns[0]: 'police_office',  # First column (police office)
                    data.columns[1]: 'barangay',  # Second column (barangay)
                    data.columns[2]: 'date_committed',  # Third column (date)
                    data.columns[3]: 'time_committed',  # Fourth column (time)
                    data.columns[4]: 'offense',  # Fifth column (offense)
                    data.columns[5]: 'latitude',  # Sixth column (latitude)
                    data.columns[6]: 'longitude'  # Seventh column (longitude)
                }

                data = data.rename(columns=column_mapping)

                # Extract city from police office (e.g., "BUTUAN CITY POLICE OFFICE" -> "BUTUAN CITY")
                def extract_city(police_office):
                    # Common pattern is "CITY NAME POLICE OFFICE/STATION"
                    if pd.isna(police_office):
                        return "Unknown City"

                    office_str = str(police_office).upper()
                    if "CITY" in office_str:
                        # Try to extract city name
                        city_parts = office_str.split("CITY")[0].strip() + " CITY"
                        return city_parts
                    else:
                        # If can't extract, use the first part of the string
                        return office_str.split()[0] if len(office_str.split()) > 0 else "Unknown City"

                # Add city column based on police office
                data['city'] = data['police_office'].apply(extract_city)

                # Fill missing values with appropriate defaults
                data['barangay'] = data['barangay'].fillna('Unknown Barangay')
                data['offense'] = data['offense'].fillna('Unspecified Offense')

                # First, count occurrences of each offense type
                offense_counts = {}
                for _, row in data.iterrows():
                    offense_type = row['offense']

                    # Count by offense type
                    if offense_type not in offense_counts:
                        offense_counts[offense_type] = 0
                    offense_counts[offense_type] += 1

                # Process data in batches to avoid memory issues
                batch_size = 1000
                crime_data_list = []

                for i in range(0, len(data), batch_size):
                    batch = data.iloc[i:i + batch_size]
                    batch_crimes = []

                    for _, row in batch.iterrows():
                        try:
                            # Parse date_committed
                            try:
                                if pd.isna(row['date_committed']):
                                    # Use current date if missing
                                    date_committed = datetime.now().date()
                                else:
                                    date_committed = pd.to_datetime(row['date_committed']).date()
                            except:
                                return HttpResponse(
                                    f"Error: Invalid date format '{row['date_committed']}' in row {_ + 1}. Use YYYY-MM-DD format.",
                                    status=400)

                            # Parse time_committed if available
                            time_committed = None
                            if pd.notna(row['time_committed']):
                                try:
                                    time_committed = pd.to_datetime(row['time_committed']).time()
                                except:
                                    # If time parsing fails, just leave it as None
                                    pass

                            # Calculate severity based on offense type AND frequency
                            offense_type = row['offense']
                            count = offense_counts.get(offense_type, 0)
                            severity = determine_severity_by_frequency(
                                offense_type,
                                count,
                                row['city'],
                                row['barangay']
                            )

                            # Convert latitude and longitude to float
                            try:
                                latitude = float(row['latitude']) if pd.notna(row['latitude']) else None
                                longitude = float(row['longitude']) if pd.notna(row['longitude']) else None
                            except ValueError:
                                latitude = None
                                longitude = None

                            batch_crimes.append(CrimeData(
                                city=row['city'],
                                barangay=row['barangay'],
                                date_committed=date_committed,
                                time_committed=time_committed,
                                offense=offense_type,
                                latitude=latitude,
                                longitude=longitude,
                                severity=severity
                            ))
                        except ValueError as ve:
                            return HttpResponse(f"Error processing row {_ + 1}: {ve}", status=400)
                        except Exception as e:
                            return HttpResponse(f"Unexpected error processing row {_ + 1}: {e}", status=400)

                    # Save batch to database
                    CrimeData.objects.bulk_create(batch_crimes)
                    crime_data_list.extend(batch_crimes)

                    # Show progress message
                    messages.info(request, f"Processed {min(i + batch_size, len(data))} of {len(data)} records...")

                # Perform K-Means clustering with 87 clusters (one for each offense type)
                apply_kmeans(87)  # Pass the number of clusters

                # Log the activity
                log_activity(
                    user=request.user,
                    action_type='upload',
                    description=f"Uploaded CSV with {len(crime_data_list)} records",
                    records_affected=len(crime_data_list),
                    request=request
                )

                messages.success(request, f"CSV file uploaded successfully! {len(crime_data_list)} records imported.")
                return redirect('result')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return HttpResponse(f"An error occurred: {e}", status=400)
    else:
        form = CSVUploadForm()

    return render(request, template, {'form': form})


def apply_kmeans(n_clusters=87):
    """
    Perform K-Means clustering on CrimeData objects based on offense type.
    Updates the `cluster` field for each CrimeData object.

    Args:
        n_clusters: Number of clusters to create (default is 87 for 87 offense types)
    """
    # Fetch all crime records
    crime_records = CrimeData.objects.all().values('id', 'offense')

    # Convert to DataFrame
    df = pd.DataFrame(list(crime_records))

    if df.empty:
        print("No crime data available for clustering")
        return  # No data for clustering

    # Create a mapping of offense types to numeric values
    unique_offense_types = df['offense'].dropna().unique()
    offense_type_mapping = {offense_type: i for i, offense_type in enumerate(unique_offense_types)}

    # Add a default value for NaN offense types
    if df['offense'].isna().any():
        offense_type_mapping[None] = len(offense_type_mapping)

    # Convert offense types to numeric values, handling NaN values
    df['offense_numeric'] = df['offense'].map(
        lambda x: offense_type_mapping.get(x, offense_type_mapping.get(None, 0)) if pd.notna(
            x) else offense_type_mapping.get(None, 0))

    # IMPORTANT: Use only offense_numeric for clustering
    # This ensures clustering is based solely on offense type
    features = np.array(df['offense_numeric']).reshape(-1, 1)

    # Check for NaN values
    if np.isnan(features).any():
        print("Warning: NaN values found in features")
        features = np.nan_to_num(features)

    # Determine optimal number of clusters (use number of unique offenses)
    n_clusters = min(n_clusters, len(offense_type_mapping))
    n_clusters = max(1, n_clusters)  # Ensure at least 1 cluster

    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(features)

    # Update the database with cluster assignments
    # Use bulk_update for better performance with large datasets
    batch_size = 1000  # Process in batches to avoid memory issues

    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i + batch_size]
        crime_objects = []

        for _, row in batch_df.iterrows():
            crime = CrimeData(id=row['id'], cluster=row['cluster'])
            crime_objects.append(crime)

        CrimeData.objects.bulk_update(crime_objects, ['cluster'])

    # Map clusters back to offense types for better interpretability
    cluster_to_offense = {}
    for cluster_id in range(n_clusters):
        cluster_data = df[df['cluster'] == cluster_id]
        if not cluster_data.empty:
            most_common_offense = cluster_data['offense'].value_counts().idxmax()
            cluster_to_offense[cluster_id] = most_common_offense

    print(f"Clustering complete with {n_clusters} clusters.")
    print("Cluster to offense mapping:")
    for cluster_id, offense in cluster_to_offense.items():
        print(f"Cluster {cluster_id}: {offense}")

    return True


def identify_crime_patterns(crimes):
    """
    Identify patterns in crime data based on location, time, crime type, and severity.
    Returns a list of pattern descriptions.
    """
    patterns = []

    # Check if we have enough data to identify patterns
    if crimes.count() < 5:
        return ["Not enough data to identify reliable patterns."]

    # Location-based patterns (city and barangay)
    city_counts = Counter([crime.city for crime in crimes])
    for city, count in city_counts.most_common(3):
        if count >= 3:  # At least 3 crimes in the same city
            percentage = (count / crimes.count()) * 100
            patterns.append(f"High crime concentration in {city} ({count} incidents, {percentage:.1f}% of total)")

    barangay_counts = Counter([crime.barangay for crime in crimes])
    for barangay, count in barangay_counts.most_common(3):
        if count >= 3:  # At least 3 crimes in the same barangay
            percentage = (count / crimes.count()) * 100
            patterns.append(
                f"High crime concentration in Barangay {barangay} ({count} incidents, {percentage:.1f}% of total)")

    # Time-based patterns
    month_counts = Counter([crime.date_committed.month for crime in crimes])
    for month, count in month_counts.most_common(2):
        if count >= 3:  # At least 3 crimes in the same month
            month_name = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }[month]
            percentage = (count / crimes.count()) * 100
            patterns.append(f"Crime spike in {month_name} ({count} incidents, {percentage:.1f}% of total)")

    # Time of day patterns (if time_committed is available)
    time_periods = {
        'Morning (6AM-12PM)': 0,
        'Afternoon (12PM-6PM)': 0,
        'Evening (6PM-12AM)': 0,
        'Night (12AM-6AM)': 0
    }

    time_data_count = 0
    for crime in crimes:
        if crime.time_committed:
            time_data_count += 1
            hour = crime.time_committed.hour
            if 6 <= hour < 12:
                time_periods['Morning (6AM-12PM)'] += 1
            elif 12 <= hour < 18:
                time_periods['Afternoon (12PM-6PM)'] += 1
            elif 18 <= hour < 24:
                time_periods['Evening (6PM-12AM)'] += 1
            else:
                time_periods['Night (12AM-6AM)'] += 1

    if time_data_count > 0:
        most_common_time = max(time_periods.items(), key=lambda x: x[1])
        if most_common_time[1] > 0:
            percentage = (most_common_time[1] / time_data_count) * 100
            patterns.append(
                f"Most crimes occur during {most_common_time[0]} ({most_common_time[1]} incidents, {percentage:.1f}% of total)")

    # Crime type patterns
    offense_counts = Counter([crime.offense for crime in crimes])
    for offense, count in offense_counts.most_common(2):
        if count >= 3:  # At least 3 crimes of the same type
            percentage = (count / crimes.count()) * 100
            patterns.append(f"Predominant offense type: {offense} ({count} incidents, {percentage:.1f}% of total)")

    # Severity patterns
    severity_counts = Counter([crime.severity for crime in crimes if crime.severity])
    for severity, count in severity_counts.most_common(1):
        percentage = (count / crimes.count()) * 100
        patterns.append(f"Predominant severity level: {severity} ({count} incidents, {percentage:.1f}% of total)")

        # Add specific insights for high severity crimes
        if severity == 'High' and percentage > 20:
            patterns.append("CRITICAL: High proportion of severe crimes requires immediate attention")
        elif severity == 'High' and percentage > 10:
            patterns.append("WARNING: Notable number of severe crimes detected")

    # If no patterns were found
    if not patterns:
        patterns.append("No significant patterns detected in the current data set.")

    return patterns


def get_action_recommendations(crimes):
    """
    Generate action recommendations based on crime severity and patterns.
    Returns a list of recommendation strings.
    """
    recommendations = []

    # Count crimes by severity
    high_severity_count = crimes.filter(severity='High').count()
    medium_severity_count = crimes.filter(severity='Medium').count()
    low_severity_count = crimes.filter(severity='Low').count()

    # Calculate percentages
    total_crimes = crimes.count()
    if total_crimes > 0:
        high_severity_percentage = (high_severity_count / total_crimes) * 100
        medium_severity_percentage = (medium_severity_count / total_crimes) * 100

        # Generate recommendations based on severity
        if high_severity_percentage >= 10:
            recommendations.append("Immediate police intervention required due to high number of severe crimes.")
            recommendations.append("Increase patrol frequency in affected areas.")
            recommendations.append("Establish community watch programs in high-risk neighborhoods.")
        elif high_severity_percentage > 0:
            recommendations.append("Increase police presence in areas with severe crimes.")
            recommendations.append("Conduct targeted investigations for severe crime incidents.")

        if medium_severity_percentage >= 20:
            recommendations.append("Implement preventive measures for assault and robbery incidents.")
            recommendations.append("Improve street lighting in affected areas.")
            recommendations.append("Consider installing surveillance cameras in high-risk locations.")
        elif medium_severity_percentage > 0:
            recommendations.append("Monitor areas with medium severity crimes for potential escalation.")

        # Location-based recommendations
        city_counts = crimes.values('city').annotate(count=Count('id')).order_by('-count')
        if city_counts.exists():
            top_city = city_counts[0]
            if top_city['count'] >= 3:
                recommendations.append(
                    f"Focus resources on {top_city['city']} which has the highest crime concentration.")

        barangay_counts = crimes.values('barangay').annotate(count=Count('id')).order_by('-count')
        if barangay_counts.exists():
            top_barangay = barangay_counts[0]
            if top_barangay['count'] >= 3:
                recommendations.append(
                    f"Increase patrols in Barangay {top_barangay['barangay']} which has high crime incidents.")

        # Time-based recommendations
        month_counts = crimes.values('date_committed__month').annotate(count=Count('id')).order_by('-count')
        if month_counts.exists():
            top_month = month_counts[0]
            month_name = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }[top_month['date_committed__month']]
            if top_month['count'] >= 3:
                recommendations.append(
                    f"Increase vigilance during {month_name} when crime rates are historically higher.")

    # If no recommendations were generated
    if not recommendations:
        recommendations.append("No specific actions recommended based on current data.")

    return recommendations


# New functions for growth analytics
def calculate_year_over_year_growth(crimes):
    """
    Calculate year-over-year growth in crime incidents.
    Returns a dictionary with years as keys and growth data as values.
    """
    # Group crimes by year
    years_data = {}
    for crime in crimes:
        year = crime.date_committed.year
        if year not in years_data:
            years_data[year] = 0
        years_data[year] += 1

    # Calculate growth rates
    growth_data = {}
    sorted_years = sorted(years_data.keys())

    for i in range(1, len(sorted_years)):
        current_year = sorted_years[i]
        prev_year = sorted_years[i - 1]
        current_count = years_data[current_year]
        prev_count = years_data[prev_year]

        if prev_count > 0:
            growth_rate = ((current_count - prev_count) / prev_count) * 100
        else:
            growth_rate = 100  # If previous year had 0 crimes, set growth rate to 100%

        growth_data[current_year] = {
            'current_count': current_count,
            'prev_count': prev_count,
            'growth_rate': growth_rate,
            'prev_year': prev_year
        }

    return growth_data


def calculate_month_over_month_growth(crimes, year=None):
    """
    Calculate month-over-month growth in crime incidents for a specific year.
    If year is None, returns data for all years.
    Returns a dictionary with years and months as keys and growth data as values.
    """
    # Group crimes by year and month
    year_month_data = {}

    for crime in crimes:
        crime_year = crime.date_committed.year
        crime_month = crime.date_committed.month

        if crime_year not in year_month_data:
            year_month_data[crime_year] = {}

        if crime_month not in year_month_data[crime_year]:
            year_month_data[crime_year][crime_month] = 0

        year_month_data[crime_year][crime_month] += 1

    # If a specific year is requested, filter to just that year
    target_years = [year] if year is not None and year in year_month_data else list(year_month_data.keys())

    # Calculate growth rates for each month in each target year
    growth_data = {}

    for target_year in target_years:
        if target_year not in year_month_data:
            continue

        growth_data[target_year] = {}

        for month in range(2, 13):  # Start from February (month 2)
            if month in year_month_data[target_year] and month - 1 in year_month_data[target_year]:
                current_count = year_month_data[target_year][month]
                prev_count = year_month_data[target_year][month - 1]

                if prev_count > 0:
                    growth_rate = ((current_count - prev_count) / prev_count) * 100
                else:
                    growth_rate = 100  # If previous month had 0 crimes, set growth rate to 100%

                growth_data[target_year][month] = {
                    'current_count': current_count,
                    'prev_count': prev_count,
                    'growth_rate': growth_rate,
                    'month_name': {
                        1: 'January', 2: 'February', 3: 'March', 4: 'April',
                        5: 'May', 6: 'June', 7: 'July', 8: 'August',
                        9: 'September', 10: 'October', 11: 'November', 12: 'December'
                    }[month],
                    'year': target_year
                }

    return growth_data


def calculate_crime_type_growth(crimes):
    """
    Calculate growth in different crime types over time.
    Returns a dictionary with crime types as keys and growth data as values.
    """
    # Group crimes by year and type
    year_type_data = {}

    for crime in crimes:
        year = crime.date_committed.year
        offense_type = crime.offense

        if year not in year_type_data:
            year_type_data[year] = {}

        if offense_type not in year_type_data[year]:
            year_type_data[year][offense_type] = 0

        year_type_data[year][offense_type] += 1

    # Calculate growth for each crime type across years
    growth_data = {}
    sorted_years = sorted(year_type_data.keys())

    if len(sorted_years) < 2:
        return {}  # Need at least 2 years to calculate growth

    # Get all unique crime types
    all_offense_types = set()
    for year_data in year_type_data.values():
        all_offense_types.update(year_data.keys())

    # Calculate growth for each crime type
    for offense_type in all_offense_types:
        growth_data[offense_type] = []

        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            prev_year = sorted_years[i - 1]

            current_count = year_type_data[current_year].get(offense_type, 0)
            prev_count = year_type_data[prev_year].get(offense_type, 0)

            if prev_count > 0:
                growth_rate = ((current_count - prev_count) / prev_count) * 100
            else:
                growth_rate = 100 if current_count > 0 else 0

            growth_data[offense_type].append({
                'year': current_year,
                'prev_year': prev_year,
                'current_count': current_count,
                'prev_count': prev_count,
                'growth_rate': growth_rate
            })

    return growth_data


def get_crime_trends_by_month(crimes):
    """
    Analyze crime trends by month across all available years.
    Returns monthly averages and identifies seasonal patterns.
    """
    # Group crimes by month
    monthly_counts = {}
    month_year_counts = {}

    for crime in crimes:
        month = crime.date_committed.month
        year = crime.date_committed.year

        if month not in monthly_counts:
            monthly_counts[month] = 0
            month_year_counts[month] = {}

        if year not in month_year_counts[month]:
            month_year_counts[month][year] = 0

        monthly_counts[month] += 1
        month_year_counts[month][year] += 1

    # Calculate average, min, max for each month
    month_stats = {}
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }

    for month in range(1, 13):
        if month in month_year_counts:
            year_counts = list(month_year_counts[month].values())
            avg_count = sum(year_counts) / len(year_counts)

            month_stats[month] = {
                'name': month_names[month],
                'total': monthly_counts.get(month, 0),
                'avg': avg_count,
                'min': min(year_counts) if year_counts else 0,
                'max': max(year_counts) if year_counts else 0,
                'years_data': month_year_counts[month]
            }
        else:
            month_stats[month] = {
                'name': month_names[month],
                'total': 0,
                'avg': 0,
                'min': 0,
                'max': 0,
                'years_data': {}
            }

    # Identify seasonal patterns (high and low seasons)
    avg_counts = [month_stats[m]['avg'] for m in range(1, 13)]
    overall_avg = sum(avg_counts) / 12 if avg_counts else 0

    high_season_months = [m for m in range(1, 13) if month_stats[m]['avg'] > overall_avg * 1.2]
    low_season_months = [m for m in range(1, 13) if month_stats[m]['avg'] < overall_avg * 0.8]

    seasonal_insights = {
        'overall_monthly_avg': overall_avg,
        'high_season': [month_names[m] for m in high_season_months],
        'low_season': [month_names[m] for m in low_season_months]
    }

    return {
        'month_stats': month_stats,
        'seasonal_insights': seasonal_insights
    }


# Update the result_view function to include the new analytics data
@login_required
def result_view(request):
    template = 'admin/result.html' if request.user.is_superuser else 'user/result_user.html'

    # Get all crimes - use pagination for large datasets
    page_size = 1000  # Adjust based on your server capacity

    # Apply filters - check both GET and POST parameters
    if request.method == 'POST':
        year_filter = request.POST.get('year')
        month_filter = request.POST.get('month')
        city_filter = request.POST.get('city')
        barangay_filter = request.POST.get('barangay')
        cluster_filter = request.POST.get('cluster')
        offense_filter = request.POST.get('offense')
        severity_filter = request.POST.get('severity')
    else:
        year_filter = request.GET.get('year')
        month_filter = request.GET.get('month')
        city_filter = request.GET.get('city')
        barangay_filter = request.GET.get('barangay')
        cluster_filter = request.GET.get('cluster')
        offense_filter = request.GET.get('offense')
        severity_filter = request.GET.get('severity')

    no_coords = request.GET.get('no_coords') == 'true'  # Parameter for AJAX request

    # Build filter query
    filter_query = Q()
    if year_filter:
        filter_query &= Q(date_committed__year=year_filter)
    if month_filter:
        filter_query &= Q(date_committed__month=month_filter)
    if city_filter:
        filter_query &= Q(city=city_filter)
    if barangay_filter:
        filter_query &= Q(barangay=barangay_filter)
    if cluster_filter:
        filter_query &= Q(cluster=cluster_filter)
    if offense_filter:
        filter_query &= Q(offense=offense_filter)
    if severity_filter:
        filter_query &= Q(severity=severity_filter)

    # Apply filters efficiently
    crimes = CrimeData.objects.filter(filter_query)

    # If this is an AJAX request for records without coordinates
    if no_coords:
        # Get records without coordinates
        records_without_coords = crimes.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True) | Q(latitude=0) | Q(longitude=0))[
                                 :100]  # Limit to 100 records for performance

        # Prepare data for JSON response
        records_data = []
        for record in records_without_coords:
            records_data.append({
                'id': record.id,
                'offense': record.offense,
                'city': record.city,
                'barangay': record.barangay,
                'date': record.date_committed.strftime('%Y-%m-%d'),
                'severity': record.severity or 'Unknown'
            })

        # Return JSON response
        return JsonResponse({
            'records': records_data,
            'total': records_without_coords.count()
        })

    # Get total count for pagination
    total_count = crimes.count()

    # Count records with and without coordinates
    records_with_coords = crimes.exclude(
        Q(latitude__isnull=True) | Q(longitude__isnull=True) | Q(latitude=0) | Q(longitude=0)).count()
    records_without_coords = total_count - records_with_coords

    # Prepare the filtered crimes to be displayed on map
    # Important: We need to ensure we're getting ALL records that match the filter criteria
    # and have valid coordinates, without any pagination limitation
    all_mappable_crimes = crimes.exclude(
        Q(latitude__isnull=True) | Q(longitude__isnull=True) | Q(latitude=0) | Q(longitude=0))

    # Get distinct values for filters - use values_list with distinct for better performance
    available_years = crimes.dates('date_committed', 'year').distinct().values_list('date_committed__year', flat=True)
    available_months = crimes.dates('date_committed', 'month').distinct().values_list('date_committed__month',
                                                                                      flat=True)
    available_cities = crimes.values_list('city', flat=True).distinct()
    available_barangays = crimes.values_list('barangay', flat=True).distinct()
    available_clusters = crimes.values_list('cluster', flat=True).distinct().exclude(cluster__isnull=True)
    available_offenses = crimes.values_list('offense', flat=True).distinct()
    available_severities = crimes.values_list('severity', flat=True).distinct().exclude(severity__isnull=True)

    # Prepare chart data - limit to top N for better performance
    max_chart_items = max(int(total_count * 0.9), 100)  # Limit chart data for better performance

    # Get offense counts for pie chart
    offense_counts = list(crimes.values('offense')
                          .annotate(count=Count('id'))
                          .order_by('-count')[:max_chart_items])
    pie_labels = [item['offense'] for item in offense_counts]
    pie_values = [item['count'] for item in offense_counts]

    # Get city counts for bar chart
    city_counts = list(crimes.values('city')
                       .annotate(count=Count('id'))
                       .order_by('-count')[:max_chart_items])
    bar_labels = [item['city'] for item in city_counts]
    bar_values = [item['count'] for item in city_counts]

    # Prepare time series data - sample for better performance with large datasets
    if total_count > 10000:
        # For large datasets, aggregate by month and year
        time_series = list(crimes.values('date_committed__year', 'date_committed__month')
                           .annotate(count=Count('id'))
                           .order_by('date_committed__year', 'date_committed__month'))
    else:
        # For smaller datasets, use full granularity
        time_series = list(crimes.values('date_committed__year', 'date_committed__month')
                           .annotate(count=Count('id'))
                           .order_by('date_committed__year', 'date_committed__month'))

    line_labels = [f"{item['date_committed__month']}/{item['date_committed__year']}" for item in time_series]
    line_values = [item['count'] for item in time_series]

    # Prepare severity distribution data
    severity_counts = list(crimes.values('severity').annotate(count=Count('id')))
    severity_labels = [item['severity'] for item in severity_counts if item['severity']]
    severity_values = [item['count'] for item in severity_counts if item['severity']]

    # Identify crime patterns - use a sample for large datasets
    if total_count > 10000:
        # Use a sample for pattern identification
        sample_size = 5000
        crime_sample = crimes.order_by('?')[:sample_size]
        crime_patterns = identify_crime_patterns(crime_sample)
    else:
        crime_patterns = identify_crime_patterns(crimes)

    # Get action recommendations based on crime severity
    action_recommendations = get_action_recommendations(crimes)

    # Calculate overall crime severity
    high_severity_count = crimes.filter(severity='High').count()
    medium_severity_count = crimes.filter(severity='Medium').count()
    low_severity_count = crimes.filter(severity='Low').count()
    total_crimes = total_count

    # Calculate severity percentages
    high_severity_percentage = (high_severity_count / total_crimes) * 100 if total_crimes > 0 else 0
    medium_severity_percentage = (medium_severity_count / total_crimes) * 100 if total_crimes > 0 else 0
    low_severity_percentage = (low_severity_count / total_crimes) * 100 if total_crimes > 0 else 0

    if total_crimes > 0:
        if high_severity_percentage >= 10:
            overall_severity = "High"
        elif high_severity_percentage > 0 or medium_severity_percentage >= 20:
            overall_severity = "Medium"
        else:
            overall_severity = "Low"
    else:
        overall_severity = "Unknown"

    # Find crime type with highest severity count
    high_severity_crimes = crimes.filter(severity='High')
    high_severity_offense_types = high_severity_crimes.values('offense').annotate(count=Count('id')).order_by('-count')
    most_severe_offense_type = high_severity_offense_types[0][
        'offense'] if high_severity_offense_types.exists() else "None"
    most_severe_offense_count = high_severity_offense_types[0]['count'] if high_severity_offense_types.exists() else 0

    # Find most common crime type
    most_common_offense_type_data = crimes.values('offense').annotate(count=Count('id')).order_by('-count').first()
    most_common_offense_type = most_common_offense_type_data['offense'] if most_common_offense_type_data else "None"

    # Prepare location severity data - use efficient aggregation
    location_severity_data = []

    # Use aggregation for better performance
    city_severity_counts = crimes.values('city').annotate(
        high=Count('id', filter=Q(severity='High')),
        medium=Count('id', filter=Q(severity='Medium')),
        low=Count('id', filter=Q(severity='Low'))
    ).order_by('-high')

    for city_data in city_severity_counts:
        location_severity_data.append({
            'name': city_data['city'],
            'high': city_data['high'],
            'medium': city_data['medium'],
            'low': city_data['low'],
        })

    # Paginate the location severity data
    locations_per_page = int(request.GET.get('locations_per_page', 5))  # Default 5 locations per page
    location_page = request.GET.get('location_page', 1)

    location_paginator = Paginator(location_severity_data, locations_per_page)
    try:
        paginated_location_data = location_paginator.page(location_page)
    except:
        paginated_location_data = location_paginator.page(1)

    # Check if this is an AJAX request for locations
    if request.GET.get('ajax') == 'true':
        # Prepare pagination info for the AJAX response
        pagination_info = {
            'current_page': paginated_location_data.number,
            'num_pages': location_paginator.num_pages,
            'has_next': paginated_location_data.has_next(),
            'has_previous': paginated_location_data.has_previous(),
            'next_page': paginated_location_data.next_page_number() if paginated_location_data.has_next() else None,
            'previous_page': paginated_location_data.previous_page_number() if paginated_location_data.has_previous() else None,
            'start_index': paginated_location_data.start_index(),
            'end_index': paginated_location_data.end_index(),
            'total_items': len(location_severity_data)
        }

        # Return JSON response
        return JsonResponse({
            'locations': list(paginated_location_data.object_list),
            'pagination': pagination_info
        })

    # Calculate growth analytics - use efficient methods for large datasets
    if total_count > 10000:
        # For large datasets, use a sample or aggregated data
        sample_crimes = crimes.order_by('?')[:5000]
        year_over_year_growth = calculate_year_over_year_growth(sample_crimes)

        # Get month-over-month growth for all years
        month_over_month_growth = calculate_month_over_month_growth(sample_crimes, None)

        # Calculate crime type growth with sample
        crime_type_growth = calculate_crime_type_growth(sample_crimes)

        # Get monthly crime trends with sample
        monthly_crime_trends = get_crime_trends_by_month(sample_crimes)
    else:
        # For smaller datasets, use all data
        year_over_year_growth = calculate_year_over_year_growth(crimes)

        # Get month-over-month growth for all years
        month_over_month_growth = calculate_month_over_month_growth(crimes, None)

        # Calculate crime type growth
        crime_type_growth = calculate_crime_type_growth(crimes)

        # Get monthly crime trends
        monthly_crime_trends = get_crime_trends_by_month(crimes)

    # Prepare context
    context = {
        'crimes': all_mappable_crimes,  # Use the full filtered list with coordinates
        'pie_labels': json.dumps(pie_labels),
        'pie_values': json.dumps(pie_values),
        'bar_labels': json.dumps(bar_labels),
        'bar_values': json.dumps(bar_values),
        'line_labels': json.dumps(line_labels),
        'line_values': json.dumps(line_values),
        'severity_labels': json.dumps(severity_labels),
        'severity_values': json.dumps(severity_values),
        'available_years': available_years,
        'available_months': available_months,
        'available_cities': available_cities,
        'available_barangays': available_barangays,
        'available_clusters': available_clusters,
        'available_offenses': available_offenses,
        'available_severities': available_severities,
        'selected_year': year_filter,
        'selected_month': month_filter,
        'selected_city': city_filter,
        'selected_barangay': barangay_filter,
        'selected_cluster': cluster_filter,
        'selected_offense': offense_filter,
        'selected_severity': severity_filter,
        'crime_patterns': crime_patterns,
        'action_recommendations': action_recommendations,
        'overall_severity': overall_severity,
        'high_severity_count': high_severity_count,
        'medium_severity_count': medium_severity_count,
        'low_severity_count': low_severity_count,
        'high_severity_percentage': high_severity_percentage,
        'medium_severity_percentage': medium_severity_percentage,
        'low_severity_percentage': low_severity_percentage,
        'most_severe_offense_type': most_severe_offense_type,
        'most_severe_offense_count': most_severe_offense_count,
        'most_common_offense_type': most_common_offense_type,
        'location_severity_data': location_severity_data,
        'paginated_location_data': paginated_location_data,
        'locations_per_page': locations_per_page,
        # New growth analytics data
        'year_over_year_growth': year_over_year_growth,
        'month_over_month_growth': month_over_month_growth,
        'crime_type_growth': crime_type_growth,
        'monthly_crime_trends': monthly_crime_trends,
        'total_crimes': total_crimes,
        'records_with_coords': records_with_coords,
        'records_without_coords': records_without_coords,
    }

    return render(request, template, context)


@login_required
def data_overview(request):
    # Get the search query
    query = request.GET.get('q', '')

    # Fetch all data
    data = CrimeData.objects.all()

    # Apply search filter if a query is provided
    if query:
        data = data.filter(
            Q(offense__icontains=query) |
            Q(city__icontains=query) |
            Q(barangay__icontains=query) |
            Q(time_committed__icontains=query) |
            Q(date_committed__icontains=query)
        )

    # Paginate the data
    paginator = Paginator(data, 10)  # Show 10 items per page
    page_number = request.GET.get('page')  # Get the current page number from the request
    page_obj = paginator.get_page(page_number)  # Get the Page object for the current page

    # Determine the template based on user role
    template = 'admin/data_overview.html' if request.user.is_superuser else 'user/data_overview_user.html'

    # Pass the paginated data and query to the template
    context = {
        'data': page_obj,  # Pass the Page object instead of the full queryset
        'query': query,
    }
    return render(request, template, context)


@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def edit_data(request, id):
    crime = get_object_or_404(CrimeData, id=id)

    if request.method == 'POST':
        # Print the raw POST data to see what's being submitted
        print("Raw POST data:")
        for key, value in request.POST.items():
            print(f"{key}: {value}")

        # Store the original values for comparison
        original_city = crime.city

        form = CrimeDataForm(request.POST, instance=crime)
        if form.is_valid():
            try:
                # Save the form directly 
                updated_crime = form.save()

                # Verify the update by re-fetching from database
                refreshed_crime = CrimeData.objects.get(id=id)
                print(f"After save - City in database: '{refreshed_crime.city}'")

                # Log the edit activity
                log_activity(
                    user=request.user,
                    action_type='edit',
                    description=f"Edited crime record (ID: {id}) - {refreshed_crime.offense} in {refreshed_crime.city}, {refreshed_crime.barangay}",
                    records_affected=1,
                    request=request
                )

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Crime record updated successfully!',
                        'city': refreshed_crime.city
                    })
                else:
                    messages.success(request, "Crime record updated successfully!")
                    return redirect('data_overview')
            except Exception as e:
                print(f"Error saving crime record: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': str(e)}, status=500)
                else:
                    messages.error(request, f"Error saving record: {str(e)}")
        else:
            print(f"Form validation errors: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                error_dict = {field: errors[0] for field, errors in form.errors.items()}
                return JsonResponse({'success': False, 'errors': error_dict}, status=400)
            else:
                messages.error(request, "Form has errors. Please correct them.")
    else:
        form = CrimeDataForm(instance=crime)

    # Use the admin template path
    template = 'admin/edit_data.html'
    return render(request, template, {'form': form})


@login_required
def delete_data(request, id):
    crime = get_object_or_404(CrimeData, id=id)
    crime_desc = f"{crime.offense} in {crime.city}, {crime.barangay} on {crime.date_committed.strftime('%m/%d/%Y')}"
    crime.delete()

    # Log the delete activity
    log_activity(
        user=request.user,
        action_type='delete',
        description=f"Deleted crime record - {crime_desc}",
        records_affected=1,
        request=request
    )

    return redirect('data_overview')


# User Management Views
@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def manage_users_view(request):
    users = User.objects.filter(is_superuser=False)
    for user in users:
        user.fullname = f"{user.first_name} {user.last_name}"
    return render(request, 'admin/manage_users.html', {'users': users})


@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def create_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = False
            user.save()

            # Log the user creation
            log_activity(
                user=request.user,
                action_type='user',
                description=f"Created new user account for {user.username}",
                request=request
            )

            messages.success(request, "User created successfully!")
            return redirect('manage_users')
        else:
            messages.error(request, "Error creating user. Please correct the issues.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'admin/create_user.html', {'form': form})


@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.is_superuser:
        messages.error(request, "Editing superuser accounts is not allowed.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        # Check which form was submitted
        if 'update_user_info' in request.POST:
            user_form = CustomUserEditForm(request.POST, instance=user)
            password_form = CustomPasswordChangeForm(user=user)  # Empty form, not validating

            if user_form.is_valid():
                user_form.save()

                # Log the activity
                log_activity(
                    user=request.user,
                    action_type='user',
                    description=f"Updated user information for {user.username}",
                    request=request
                )

                messages.success(request, "User details updated successfully.")
                return redirect('manage_users')
            else:
                # If form is invalid, we'll render it again with errors
                messages.error(request, "Please correct the errors below.")

        elif 'update_user_password' in request.POST:
            # For password update, we need to create a simpler form that just handles password
            # The built-in SetPasswordForm is better for admin changing user passwords
            from django.contrib.auth.forms import SetPasswordForm
            password_form = SetPasswordForm(user=user, data=request.POST)
            user_form = CustomUserEditForm(instance=user)  # Empty form, not validating

            if password_form.is_valid():
                password_form.save()

                # Log the activity
                log_activity(
                    user=request.user,
                    action_type='user',
                    description=f"Updated password for {user.username}",
                    request=request
                )

                messages.success(request, "User password updated successfully.")
                return redirect('manage_users')
            else:
                # If form is invalid, we'll render it again with errors
                messages.error(request, "Please correct the password errors below.")
    else:
        user_form = CustomUserEditForm(instance=user)
        password_form = CustomPasswordChangeForm(user=user)

    return render(request, 'admin/edit_user.html', {
        'user_form': user_form,
        'password_form': password_form,
        'user': user,
    })


@login_required
def delete_user_view(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        username = user.username
        user.delete()

        # Log the user deletion
        log_activity(
            user=request.user,
            action_type='user',
            description=f"Deleted user account for {username}",
            request=request
        )

        messages.success(request, "User deleted successfully.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect('manage_users')


@login_required
def user_change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            # Remove success message to prevent banner display
            return redirect('user_dashboard')
        else:
            # Remove error message banner, we'll handle errors in the template with SweetAlert
            # messages.error(request, "There were errors in your form. Please correct them.")
            pass
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'user/user_changepassword.html', {'form': form})


@login_required
@user_passes_test(role_required('admin'), login_url='/forbidden/')
def admin_change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been successfully updated!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "There were errors in your form. Please correct them.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'admin/admin_changepass.html', {'form': form})
