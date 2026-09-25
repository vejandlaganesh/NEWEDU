from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import apps.content.models

class Migration(migrations.Migration):
    dependencies = [('content','0001_initial'), ('academics','0001_initial'), ('teachers','0001_initial')]
    operations = [migrations.CreateModel(name='LearningMaterial', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('title', models.CharField(max_length=255)), ('description', models.TextField(blank=True)),
        ('material_type', models.CharField(choices=[('PDF','PDF'),('VIDEO','Video'),('DOCUMENT','Document'),('IMAGE','Image'),('LINK','External Link'),('TEXT','Text')], default='DOCUMENT', max_length=20)),
        ('file', models.FileField(blank=True, null=True, upload_to=apps.content.models.material_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf','doc','docx','txt','png','jpg','jpeg','mp4','webm','ppt','pptx']), apps.content.models.validate_material_size])),
        ('external_url', models.URLField(blank=True)), ('text_content', models.TextField(blank=True)), ('is_published', models.BooleanField(default=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
        ('chapter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='learning_materials', to='academics.chapter')),
        ('class_subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_materials', to='academics.classsubject')),
        ('lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='learning_materials', to='academics.lesson')),
        ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_materials', to='teachers.teacherprofile')),
    ]), migrations.AddIndex(model_name='learningmaterial', index=models.Index(fields=['class_subject','is_published'], name='content_le_class_s_idx')), migrations.AddIndex(model_name='learningmaterial', index=models.Index(fields=['chapter','is_published'], name='content_le_chapter_idx'))]
