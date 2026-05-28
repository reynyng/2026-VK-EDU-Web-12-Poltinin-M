from django.contrib.postgres.search import SearchVectorField
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0001_initial'),  # Убедитесь, что имя правильное
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='search_vector',
            field=SearchVectorField(null=True),
        ),
        migrations.RunSQL(
            sql="""
                UPDATE app_question SET search_vector = 
                setweight(to_tsvector('russian', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('russian', coalesce(text, '')), 'B');
                
                CREATE INDEX question_search_vector_idx ON app_question USING GIN (search_vector);
                
                CREATE OR REPLACE FUNCTION app_question_search_vector_update() RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('russian', coalesce(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('russian', coalesce(NEW.text, '')), 'B');
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
                
                CREATE TRIGGER app_question_search_vector_trigger
                BEFORE INSERT OR UPDATE ON app_question
                FOR EACH ROW EXECUTE PROCEDURE app_question_search_vector_update();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS app_question_search_vector_trigger ON app_question;
                DROP INDEX IF EXISTS question_search_vector_idx;
                ALTER TABLE app_question DROP COLUMN IF EXISTS search_vector;
            """,
        ),
    ]