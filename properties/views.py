from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Count, Sum, Avg
from django.http import JsonResponse
from .models import Property, PropertyType, Amenity, PropertyImage, PropertyAmenity
from bookings.models import Booking
from reviews.models import Review
from visits.models import Visit
from payments.models import Payment
from .forms import PropertyForm, PropertySearchForm
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST
import json

class PropertyListView(ListView):
    model = Property
    template_name = 'properties/property_list.html'
    context_object_name = 'properties'
    paginate_by = 9
    
    def get_queryset(self):
        # Create a subquery to check for approved bookings
        approved_bookings = Booking.objects.filter(
            property=OuterRef('pk'),
            status='APPROVED'
        )

        # Start with all properties and exclude those with approved bookings
        queryset = Property.objects.filter(is_available=True).exclude(
            Exists(approved_bookings)
        ).prefetch_related(
            'images',
            'amenities__amenity'
        ).order_by('-created_at')
        
        form = PropertySearchForm(self.request.GET)
        
        if form.is_valid():
            search = form.cleaned_data.get('search')
            property_type = form.cleaned_data.get('property_type')
            min_rent = form.cleaned_data.get('min_rent')
            max_rent = form.cleaned_data.get('max_rent')
            city = form.cleaned_data.get('city')
            amenities = form.cleaned_data.get('amenities')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(address__icontains=search) |
                    Q(city__icontains=search)
                )
            
            if property_type:
                queryset = queryset.filter(property_type_id=property_type)
            
            if min_rent:
                queryset = queryset.filter(monthly_rent__gte=min_rent)
            
            if max_rent:
                queryset = queryset.filter(monthly_rent__lte=max_rent)
            
            if city:
                queryset = queryset.filter(city__icontains=city)
            
            if amenities:
                queryset = queryset.filter(amenities__amenity_id__in=amenities).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['property_types'] = PropertyType.objects.all()
        context['amenities'] = Amenity.objects.all()
        return context

class CustomerPropertyDetailView(DetailView):
    model = Property
    template_name = 'properties/customer_property_detail.html'
    context_object_name = 'property'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property = self.get_object()
        
        # Get booked dates
        booked_dates = Booking.objects.filter(
            property=property,
            status__in=['APPROVED', 'COMPLETED']
        ).values_list('start_date', flat=True)
        
        # Get scheduled visits
        scheduled_visits = Visit.objects.filter(
            property=property,
            status__in=['APPROVED'],
            visit_date__gte=timezone.now().date()
        ).values('visit_date', 'visit_time')
        
        # Check if user has already booked or visited
        if self.request.user.is_authenticated:
            context['has_booking'] = Booking.objects.filter(
                property=property,
                customer=self.request.user,
                status__in=['APPROVED', 'COMPLETED']
            ).exists()
            
            context['has_visit'] = Visit.objects.filter(
                property=property,
                customer=self.request.user,
                status__in=['REQUESTED', 'APPROVED']
            ).exists()
        
        context['booked_dates'] = list(booked_dates)
        context['scheduled_visits'] = list(scheduled_visits)
        context['reviews'] = Review.objects.filter(property=property).order_by('-created_at')
        context['similar_properties'] = Property.objects.filter(
            property_type=property.property_type,
            is_available=True
        ).exclude(id=property.id)[:3]
        
        return context

class LandlordPropertyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Property
    template_name = 'properties/landlord_property_detail.html'
    context_object_name = 'property'
    
    def test_func(self):
        property = self.get_object()
        return self.request.user == property.landlord or self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property = self.get_object()
        
        # Get upcoming visits
        context['upcoming_visits'] = Visit.objects.filter(
            property=property,
            status='APPROVED',
            visit_date__gte=timezone.now().date()
        ).order_by('visit_date', 'visit_time')
        
        # Get active bookings
        context['active_bookings'] = Booking.objects.filter(
            property=property,
            status='APPROVED'
        ).order_by('-created_at')
        
        # Get visit requests
        context['visit_requests'] = Visit.objects.filter(
            property=property,
            status='REQUESTED'
        ).order_by('visit_date', 'visit_time')
        
        # Get booking requests
        context['booking_requests'] = Booking.objects.filter(
            property=property,
            status='PENDING'
        ).order_by('-created_at')
        
        # Calculate statistics
        context['total_visits'] = Visit.objects.filter(property=property).count()
        context['total_bookings'] = Booking.objects.filter(property=property).count()
        context['total_revenue'] = Booking.objects.filter(
            property=property,
            status='COMPLETED'
        ).count() * property.monthly_rent
        
        return context

class PropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_create.html'
    success_url = reverse_lazy('landlord_properties')
    
    def test_func(self):
        return self.request.user.is_landlord() or self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['property_types'] = PropertyType.objects.all()
        context['amenities'] = Amenity.objects.all()
        return context
    
    def form_valid(self, form):
        form.instance.landlord = self.request.user
        response = super().form_valid(form)
        
        # Handle amenities
        amenities = self.request.POST.getlist('amenities')
        if amenities:
            for amenity_id in amenities:
                amenity = Amenity.objects.get(id=amenity_id)
                PropertyAmenity.objects.create(property=self.object, amenity=amenity)
        
        # Handle images
        images = self.request.FILES.getlist('images')
        primary_image_id = self.request.POST.get('primary_image')
        
        for i, image in enumerate(images):
            is_primary = str(i) == primary_image_id if primary_image_id else i == 0
            PropertyImage.objects.create(
                property=self.object,
                image=image,
                is_primary=is_primary
            )
        
        messages.success(self.request, 'Property listed successfully!')
        return response

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/property_edit.html'
    
    def test_func(self):
        property = self.get_object()
        return self.request.user == property.landlord or self.request.user.is_admin()
    
    def get_success_url(self):
        if self.request.user.is_admin():
            return reverse_lazy('manage_properties')
        return reverse_lazy('landlord_properties')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['property_types'] = PropertyType.objects.all()
        context['amenities'] = Amenity.objects.all()
        context['property'] = self.get_object()
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle amenities
        amenities = self.request.POST.getlist('amenities')
        PropertyAmenity.objects.filter(property=self.object).delete()
        if amenities:
            for amenity_id in amenities:
                amenity = Amenity.objects.get(id=amenity_id)
                PropertyAmenity.objects.create(property=self.object, amenity=amenity)
        
        # Handle images
        images = self.request.FILES.getlist('images')
        primary_image_id = self.request.POST.get('primary_image')
        
        if images:
            # Remove old images if new ones are uploaded
            self.object.images.all().delete()
            for i, image in enumerate(images):
                is_primary = str(i) == primary_image_id if primary_image_id else i == 0
                PropertyImage.objects.create(
                    property=self.object,
                    image=image,
                    is_primary=is_primary
                )
        elif primary_image_id:
            # Update primary image without uploading new images
            self.object.images.all().update(is_primary=False)
            PropertyImage.objects.filter(id=primary_image_id).update(is_primary=True)
        
        messages.success(self.request, 'Property updated successfully!')
        return response

@require_POST
def delete_property_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id)
    if request.user == image.property.landlord or request.user.is_admin():
        was_primary = image.is_primary
        image.delete()
        
        # If the deleted image was primary, make the first remaining image primary
        if was_primary:
            first_image = PropertyImage.objects.filter(property=image.property).first()
            if first_image:
                first_image.is_primary = True
                first_image.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

class PropertyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Property
    success_url = reverse_lazy('landlord_properties')
    
    def test_func(self):
        property = self.get_object()
        return self.request.user == property.landlord or self.request.user.is_admin()
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Property deleted successfully!')
        return super().delete(request, *args, **kwargs)

class LandlordPropertiesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Property
    template_name = 'properties/landlord_properties.html'
    context_object_name = 'properties'
    
    def test_func(self):
        return self.request.user.is_landlord() or self.request.user.is_admin()
    
    def get_queryset(self):
        if self.request.user.is_admin():
            return Property.objects.all().prefetch_related(
                'images',
                'amenities__amenity'
            ).order_by('-created_at')
        return Property.objects.filter(landlord=self.request.user).prefetch_related(
            'images',
            'amenities__amenity'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = self.get_queryset()
        context['available_properties'] = properties.filter(is_available=True).count()
        context['active_bookings'] = sum(p.bookings.filter(status='APPROVED').count() for p in properties)
        return context

class LandlordBookingsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Booking
    template_name = 'properties/landlord_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_landlord() or self.request.user.is_admin()

    def get_queryset(self):
        if self.request.user.is_admin():
            return Booking.objects.all().select_related(
                'property',
                'customer'
            ).order_by('-created_at')
        return Booking.objects.filter(
            property__landlord=self.request.user
        ).select_related(
            'property',
            'customer'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_bookings'] = self.get_queryset().filter(status='PENDING').count()
        context['approved_bookings'] = self.get_queryset().filter(status='APPROVED').count()
        context['completed_bookings'] = self.get_queryset().filter(status='COMPLETED').count()
        return context

def get_property_types(request):
    property_types = list(PropertyType.objects.values('id', 'name'))
    return JsonResponse({'property_types': property_types})

def get_amenities(request):
    amenities = list(Amenity.objects.values('id', 'name', 'icon'))
    return JsonResponse({'amenities': amenities})

@require_POST
def toggle_availability(request, property_id):
    try:
        property = get_object_or_404(Property, id=property_id)
        if request.user == property.landlord or request.user.is_admin():
            data = json.loads(request.body)
            property.is_available = data['is_available']
            property.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class LandlordHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'properties/landlord_home.html'
    
    def test_func(self):
        return self.request.user.is_landlord() or self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get property statistics
        if user.is_admin():
            properties = Property.objects.all()
        else:
            properties = Property.objects.filter(landlord=user)
            
        context['total_properties'] = properties.count()
        context['active_bookings'] = Booking.objects.filter(
            property__in=properties,
            status='APPROVED'
        ).count()
        context['pending_visits'] = Visit.objects.filter(
            property__in=properties,
            status='REQUESTED'
        ).count()
        
        # Calculate total revenue
        total_revenue = Payment.objects.filter(
            booking__property__in=properties,
            payment_status='COMPLETED',
            payment_type__in=['RENT', 'SECURITY_DEPOSIT']
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_revenue'] = total_revenue
        
        # Get recent bookings
        context['recent_bookings'] = Booking.objects.filter(
            property__in=properties
        ).order_by('-created_at')[:5]
        
        # Get recent reviews
        context['recent_reviews'] = Review.objects.filter(
            property__in=properties
        ).order_by('-created_at')[:5]
        
        return context