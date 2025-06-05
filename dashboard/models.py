from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver # type: ignore

class Zone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    center = models.ForeignKey('Center', on_delete=models.CASCADE, null=True)  # Modified this line

    def __str__(self):
        return self.name

class Center(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Cell(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_active_leader(self):
        return UserProfile.objects.filter(
            cell=self,
            role='cell_leader',
            user__is_active=True
        ).first()

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('zone_leader', 'Zone Leader'),
        ('cell_leader', 'Cell Leader'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)
    cell = models.ForeignKey(Cell, on_delete=models.SET_NULL, null=True, blank=True)
    center = models.ForeignKey('Center', on_delete=models.SET_NULL, null=True, blank=True)  # Add this line
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal to create/update UserProfile when User is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


class Issue(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)
    asset = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Low')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Modified this line
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='issue_images/', null=True, blank=True)
    after_image = models.ImageField(
        upload_to='issues/after/',
        null=True,
        blank=True,
        verbose_name='After Fix Image'
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Asset(models.Model):
    ASSET_TYPE_CHOICES = [  # <mcsymbol name="ASSET_TYPE_CHOICES" filename="models.py" path="dashboard/models.py" startline="108" type="class"></mcsymbol>
        ('bench', 'Bench'),
        ('light', 'Light'),
        ('table', 'Table'),
        ('chair', 'Chair'),
        ('fan', 'Fan'),
        ('board', 'Board'),
        ('tv', 'TV'),
        ('cctv', 'CCTV'),
        ('switch_board', 'Switch Board'),
        ('others', 'Others'),
    ]
    
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    asset_id = models.CharField(max_length=50)
    cell = models.ForeignKey('Cell', on_delete=models.CASCADE, related_name='assets')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cell', 'asset_type', 'asset_id']

    def __str__(self):
        return f"{self.get_asset_type_display()}-{self.asset_id}"


class RedTag(models.Model):
    DAMAGE_CATEGORIES = [
        ('structural', 'Structural Damage'),
        ('functional', 'Functional Issue'),
        ('safety', 'Safety Hazard'),
        ('cosmetic', 'Cosmetic Damage'),
    ]
    
    ACTION_REQUIRED = [
        ('repair', 'Needs Repair'),
        ('replace', 'Requires Replacement'),
        ('dispose', 'Must be Disposed'),
    ]

    issue = models.OneToOneField('Issue', on_delete=models.CASCADE)
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    damage_category = models.CharField(max_length=20, choices=DAMAGE_CATEGORIES)
    action_required = models.CharField(max_length=20, choices=ACTION_REQUIRED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

