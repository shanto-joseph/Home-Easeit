from django import forms
from .models import Property, PropertyImage
from django.utils.text import slugify

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PropertyForm(forms.ModelForm):
    images = MultipleImageField(
        required=False,
        help_text='Upload up to 6 images'
    )
    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'address', 'city', 
            'state', 'pincode', 'latitude', 'longitude', 'monthly_rent',
            'security_deposit', 'available_from'
        ]
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if self.instance.pk:  # If editing existing property
            if Property.objects.filter(slug=slugify(title)).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("A property with this title already exists.")
        else:  # If creating new property
            if Property.objects.filter(slug=slugify(title)).exists():
                raise forms.ValidationError("A property with this title already exists.")
        return title
    
    def clean_monthly_rent(self):
        monthly_rent = self.cleaned_data.get('monthly_rent')
        if monthly_rent <= 0:
            raise forms.ValidationError("Monthly rent must be greater than 0.")
        return monthly_rent
    
    def clean_security_deposit(self):
        security_deposit = self.cleaned_data.get('security_deposit')
        if security_deposit <= 0:
            raise forms.ValidationError("Security deposit must be greater than 0.")
        return security_deposit
    
    def clean_images(self):
        images = self.files.getlist('images')
        if len(images) > 6:
            raise forms.ValidationError("You can upload a maximum of 6 images.")
        for image in images:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large. Maximum size is 5MB.")
        return images

class PropertySearchForm(forms.Form):
    search = forms.CharField(required=False)
    property_type = forms.IntegerField(required=False)
    min_rent = forms.DecimalField(required=False)
    max_rent = forms.DecimalField(required=False)
    city = forms.CharField(required=False)
    amenities = forms.MultipleChoiceField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Amenity
        self.fields['amenities'].choices = [(amenity.id, amenity.name) for amenity in Amenity.objects.all()]