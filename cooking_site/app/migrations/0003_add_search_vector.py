from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('app', '0002_add_search_vector'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Обновляем существующие записи
                UPDATE app_question SET search_vector = 
                    setweight(to_tsvector('russian', coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('russian', coalesce(text, '')), 'B')
                WHERE search_vector IS NULL;
                
                -- Создаем или заменяем функцию
                CREATE OR REPLACE FUNCTION app_question_search_vector_update() RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('russian', coalesce(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('russian', coalesce(NEW.text, '')), 'B');
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
                
                -- Создаем триггер
                DROP TRIGGER IF EXISTS app_question_search_vector_trigger ON app_question;
                CREATE TRIGGER app_question_search_vector_trigger
                BEFORE INSERT OR UPDATE ON app_question
                FOR EACH ROW EXECUTE FUNCTION app_question_search_vector_update();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS app_question_search_vector_trigger ON app_question;
                DROP FUNCTION IF EXISTS app_question_search_vector_update();
            """,
        ),
    ]