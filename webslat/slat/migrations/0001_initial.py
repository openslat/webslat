# Generated by Django 2.1.3 on 2019-01-29 22:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ComponentsTab',
            fields=[
                ('key', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('ident', models.TextField(unique=True)),
                ('name', models.TextField(blank=True, null=True)),
                ('system', models.TextField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'components_tab',
            },
        ),
        migrations.CreateModel(
            name='CostTab',
            fields=[
                ('rowid', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('state', models.IntegerField(blank=True, null=True)),
                ('min_cost', models.FloatField(blank=True, null=True)),
                ('max_cost', models.FloatField(blank=True, null=True)),
                ('dispersion', models.FloatField(blank=True, null=True)),
                ('lower_limit', models.IntegerField(blank=True, null=True)),
                ('upper_limit', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'cost_tab',
            },
        ),
        migrations.CreateModel(
            name='DemandsTab',
            fields=[
                ('key', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'demands_tab',
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'managed': False,
                'db_table': 'django_migrations',
            },
        ),
        migrations.CreateModel(
            name='EDP_Flavours',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_text', models.CharField(max_length=25)),
            ],
            options={
                'managed': False,
                'db_table': 'slat_edp_flavours',
            },
        ),
        migrations.CreateModel(
            name='FragilityTab',
            fields=[
                ('rowid', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('state', models.IntegerField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('repairs', models.TextField(blank=True, null=True)),
                ('median', models.FloatField(blank=True, null=True)),
                ('beta', models.FloatField(blank=True, null=True)),
                ('image', models.TextField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'fragility_tab',
            },
        ),
        migrations.CreateModel(
            name='IM_Types',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_text', models.CharField(max_length=25)),
            ],
            options={
                'managed': False,
                'db_table': 'slat_im_types',
            },
        ),
        migrations.CreateModel(
            name='Input_File_Formats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('format_text', models.CharField(max_length=20)),
            ],
            options={
                'managed': False,
                'db_table': 'slat_input_file_formats',
            },
        ),
        migrations.CreateModel(
            name='Interpolation_Method',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method_text', models.CharField(max_length=20)),
            ],
            options={
                'managed': False,
                'db_table': 'slat_interpolation_method',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=128)),
                ('z', models.FloatField()),
                ('min_distance', models.FloatField(null=True)),
                ('max_disstance', models.FloatField(null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'slat_location',
            },
        ),
        migrations.CreateModel(
            name='PACT_CatsTab',
            fields=[
                ('rowid', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('ident', models.TextField(blank=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('formula', models.TextField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'pact_cats_tab',
            },
        ),
        migrations.CreateModel(
            name='UnitsTab',
            fields=[
                ('key', models.IntegerField(blank=True, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'units_tab',
            },
        ),
        migrations.CreateModel(
            name='Component_Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_x', models.IntegerField()),
                ('quantity_y', models.IntegerField()),
                ('quantity_u', models.IntegerField()),
                ('cost_adj', models.FloatField(default=1.0)),
                ('comment', models.CharField(blank=True, max_length=256, null=True)),
                ('component', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, to='slat.ComponentsTab')),
            ],
        ),
        migrations.CreateModel(
            name='Component_Group_Pattern',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_x', models.IntegerField()),
                ('quantity_y', models.IntegerField()),
                ('quantity_u', models.IntegerField()),
                ('cost_adj', models.FloatField(default=1.0)),
                ('comment', models.CharField(blank=True, max_length=256, null=True)),
                ('component', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, to='slat.ComponentsTab')),
            ],
        ),
        migrations.CreateModel(
            name='EDP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flavour', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='slat.EDP_Flavours')),
                ('interpolation_method', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='slat.Interpolation_Method')),
            ],
        ),
        migrations.CreateModel(
            name='EDP_Grouping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('D', 'Inter-story Drift'), ('A', 'Acceleration')], max_length=1)),
                ('demand_x', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='demand_x', to='slat.EDP')),
                ('demand_y', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='demand_y', to='slat.EDP')),
            ],
        ),
        migrations.CreateModel(
            name='EDP_Point',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('im', models.FloatField()),
                ('median_x', models.FloatField()),
                ('sd_ln_x', models.FloatField()),
                ('demand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.EDP')),
            ],
        ),
        migrations.CreateModel(
            name='EDP_PowerCurve',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('median_x_a', models.FloatField(default=0.1)),
                ('median_x_b', models.FloatField(default=1.5)),
                ('sd_ln_x_a', models.FloatField(default=0.5)),
                ('sd_ln_x_b', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ETABS_Preprocess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50, null=True)),
                ('description', models.CharField(max_length=200, null=True)),
                ('strength', models.FloatField(null=True)),
                ('location', models.CharField(max_length=50, null=True)),
                ('soil_class', models.CharField(max_length=1, null=True)),
                ('return_period', models.IntegerField()),
                ('frame_type_x', models.CharField(max_length=10, null=True)),
                ('frame_type_y', models.CharField(max_length=10, null=True)),
                ('file_name', models.CharField(max_length=255, null=True)),
                ('file_contents', models.BinaryField(null=True)),
                ('period_units', models.CharField(max_length=10, null=True)),
                ('period_x', models.FloatField(null=True)),
                ('period_y', models.FloatField(null=True)),
                ('hazard_period_source', models.CharField(max_length=10, null=True)),
                ('hazard_manual_period', models.FloatField(null=True)),
                ('height_units', models.CharField(max_length=10, null=True)),
                ('stories', models.BinaryField(null=True)),
                ('drift_case_x', models.CharField(max_length=50, null=True)),
                ('drift_case_y', models.CharField(max_length=50, null=True)),
                ('accel_units_x', models.CharField(max_length=10, null=True)),
                ('accel_units_y', models.CharField(max_length=10, null=True)),
                ('accel_case_x', models.CharField(max_length=50, null=True)),
                ('accel_case_y', models.CharField(max_length=50, null=True)),
                ('period_choices', models.BinaryField(null=True)),
                ('drift_choices', models.BinaryField(null=True)),
                ('accel_choices', models.BinaryField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='IM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flavour', models.ForeignKey(db_constraint=False, default=4097, on_delete=django.db.models.deletion.PROTECT, to='slat.IM_Types')),
                ('interp_method', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='slat.Interpolation_Method')),
            ],
        ),
        migrations.CreateModel(
            name='IM_Point',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('im_value', models.FloatField()),
                ('rate', models.FloatField()),
                ('hazard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.IM')),
            ],
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField()),
                ('label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='NonLinearHyperbolic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('v_assy_float', models.FloatField(default=1221)),
                ('im_asy_float', models.FloatField(default=29.8)),
                ('alpha_float', models.FloatField(default=62.2)),
            ],
        ),
        migrations.CreateModel(
            name='NZ_Standard_Curve',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('soil_class', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')], default='A', max_length=1)),
                ('period', models.FloatField(default=1.5)),
                ('location', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, to='slat.Location')),
            ],
            options={
                'managed': True,
                'db_table': 'slat_nz_standard_curve',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization', models.CharField(blank=True, max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_text', models.CharField(max_length=50)),
                ('description_text', models.CharField(blank=True, max_length=200)),
                ('rarity', models.FloatField(choices=[(0.05, '20'), (0.04, '25'), (0.02, '50'), (0.01, '100'), (0.004, '250'), (0.002, '500'), (0.001, '1000'), (0.0004, '2000'), (0.0004, '2500')])),
                ('mean_im_collapse', models.FloatField(blank=True, null=True)),
                ('sd_ln_im_collapse', models.FloatField(blank=True, null=True)),
                ('mean_cost_collapse', models.FloatField(blank=True, null=True)),
                ('sd_ln_cost_collapse', models.FloatField(blank=True, null=True)),
                ('mean_im_demolition', models.FloatField(blank=True, null=True)),
                ('sd_ln_im_demolition', models.FloatField(blank=True, null=True)),
                ('mean_cost_demolition', models.FloatField(blank=True, null=True)),
                ('sd_ln_cost_demolition', models.FloatField(blank=True, null=True)),
                ('IM', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='slat.IM')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectGroupPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Group')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Project')),
            ],
        ),
        migrations.CreateModel(
            name='ProjectUserPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('O', 'Full'), ('N', 'None')], default='N', max_length=1)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='level',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Project'),
        ),
        migrations.AddField(
            model_name='im',
            name='nlh',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='slat.NonLinearHyperbolic'),
        ),
        migrations.AddField(
            model_name='im',
            name='nzs',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='slat.NZ_Standard_Curve'),
        ),
        migrations.AddField(
            model_name='edp_grouping',
            name='level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Level'),
        ),
        migrations.AddField(
            model_name='edp_grouping',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Project'),
        ),
        migrations.AddField(
            model_name='edp',
            name='powercurve',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='slat.EDP_PowerCurve'),
        ),
        migrations.AddField(
            model_name='component_group_pattern',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slat.Project'),
        ),
        migrations.AddField(
            model_name='component_group',
            name='demand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='demand', to='slat.EDP_Grouping'),
        ),
        migrations.AddField(
            model_name='component_group',
            name='pattern',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='slat.Component_Group_Pattern'),
        ),
    ]
