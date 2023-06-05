from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()


class JoinChallengeForm(forms.Form):
    strava_runner_id = forms.IntegerField()
    voz_name = forms.CharField(max_length=200, required=False)
    registered_mileage_distance = forms.IntegerField(required=False)
    week_num = forms.IntegerField()
    year = forms.IntegerField()


class UpdateAfterRegForm(forms.Form):
    strava_runner_id = forms.IntegerField()
    voz_name = forms.CharField(max_length=200, required=False)
    note = forms.CharField(widget=forms.Textarea(), required=False)
    week_num = forms.IntegerField()
    year = forms.IntegerField()
