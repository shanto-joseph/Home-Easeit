from django import forms
from .models import Visit
from django.utils import timezone
from datetime import timedelta

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['visit_date', 'visit_time']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'visit_time': forms.HiddenInput()  # Changed to hidden input
        }
    
    def clean_visit_date(self):
        visit_date = self.cleaned_data.get('visit_date')
        today = timezone.now().date()
        
        if visit_date < today:
            raise forms.ValidationError("Visit date cannot be in the past.")
        
        if visit_date > today + timedelta(days=30):
            raise forms.ValidationError("Visit date cannot be more than 30 days in the future.")
        
        return visit_date
    
    def clean(self):
        cleaned_data = super().clean()
        visit_date = cleaned_data.get('visit_date')
        visit_time = cleaned_data.get('visit_time')
        
        if not hasattr(self, 'property_instance'):
            raise forms.ValidationError("Property not set for validation")
            
        if visit_date and visit_time and self.property_instance:
            # Check for existing visits at the same date and time
            existing_visits = Visit.objects.filter(
                property=self.property_instance,
                visit_date=visit_date,
                visit_time=visit_time,
                status__in=['REQUESTED', 'APPROVED', 'RESCHEDULED']
            )

            if existing_visits.exists():
                raise forms.ValidationError(
                    "This time slot is already booked. Please select a different time slot."
                )

        return cleaned_data