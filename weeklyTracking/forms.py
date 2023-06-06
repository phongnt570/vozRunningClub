from django import forms


class WeeklyRegistrationForm(forms.Form):
    week_num = forms.IntegerField()
    year = forms.IntegerField()
    registered_mileage_distance = forms.IntegerField(required=False)
    note = forms.CharField(widget=forms.Textarea(), required=False)


class UserProfileForm(forms.Form):
    voz_name = forms.CharField(max_length=255, required=False)
