from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q

FORMATO_CELULAR = r"^[0-9]{2}9[0-9]{8}$"
NOME_MINIMO = 3


class Locomocao(models.TextChoices):
    CADEIRA_DE_RODAS = "CADEIRA_DE_RODAS", "Cadeira de rodas"
    ANDADOR_BENGALA_MULETA = "ANDADOR_BENGALA_MULETA", "Andador, bengala ou muleta"
    DEFICIENCIA_VISUAL = "DEFICIENCIA_VISUAL", "Deficiência visual"
    CARRINHO_DE_BEBE = "CARRINHO_DE_BEBE", "Carrinho de bebê"
    SEM_DIFICULDADE = "SEM_DIFICULDADE", "Sem dificuldade de locomoção"
    NAO_INFORMADO = "NAO_INFORMADO", "Prefiro não informar"


class UsuarioManager(BaseUserManager):
    """Cria usuários identificados pelo e-mail, sem username (ADR 0002)."""

    use_in_migrations = True

    def create_user(self, email: str, senha: str | None = None, **campos) -> "Usuario":
        # Conta nova fica inativa até o celular ser verificado (spec 0002).
        campos.setdefault("is_active", False)
        campos.setdefault("celular_verificado", False)
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        return self._criar(email, senha, **campos)

    def create_superuser(self, email: str, password: str | None = None, **campos) -> "Usuario":
        # O parâmetro se chama "password" porque o comando createsuperuser o envia com esse nome.
        campos.setdefault("is_staff", True)
        campos.setdefault("is_superuser", True)
        campos.setdefault("is_active", True)
        campos.setdefault("celular_verificado", True)
        if campos["is_staff"] is not True or campos["is_superuser"] is not True:
            raise ValueError("O superusuário precisa ter is_staff e is_superuser verdadeiros.")
        return self._criar(email, password, **campos)

    def _criar(self, email: str, senha: str | None, **campos) -> "Usuario":
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(email=self.normalize_email(email), **campos)
        usuario.set_password(senha)
        usuario.save(using=self._db)
        return usuario


class Usuario(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField("e-mail", max_length=200, unique=True)
    nome_completo = models.CharField(
        "nome completo",
        max_length=120,
        validators=[MinLengthValidator(NOME_MINIMO)],
    )
    celular = models.CharField(
        "celular",
        max_length=11,
        unique=True,
        validators=[RegexValidator(FORMATO_CELULAR, "Informe DDD + 9 + 8 dígitos, apenas números.")],
        help_text="Apenas números: DDD + 9 + 8 dígitos. Ex.: 82912345678.",
    )
    locomocao = models.CharField(
        "forma de locomoção",
        max_length=30,
        choices=Locomocao.choices,
        default=Locomocao.NAO_INFORMADO,
    )
    # Padrão falso para respeitar ck_usuario_ativo_exige_verificacao em qualquer caminho de criação.
    is_active = models.BooleanField(
        "ativo",
        default=False,
        help_text="Só pode ficar ativo com o celular verificado.",
    )
    celular_verificado = models.BooleanField("celular verificado", default=False)
    termos_aceitos_em = models.DateTimeField("termos aceitos em", null=True, blank=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nome_completo", "celular"]

    objects = UsuarioManager()

    class Meta:
        db_table = "usuario"
        verbose_name = "usuário"
        verbose_name_plural = "usuários"
        constraints = [
            models.CheckConstraint(
                condition=Q(celular__regex=FORMATO_CELULAR),
                name="ck_usuario_celular_formato",
            ),
            models.CheckConstraint(
                condition=Q(nome_completo__length__gte=NOME_MINIMO),
                name="ck_usuario_nome_minimo",
            ),
            models.CheckConstraint(
                condition=Q(locomocao__in=Locomocao.values),
                name="ck_usuario_locomocao_valida",
            ),
            models.CheckConstraint(
                condition=Q(is_active=False) | Q(celular_verificado=True),
                name="ck_usuario_ativo_exige_verificacao",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    # first_name e last_name foram removidos; o Django usa estes métodos no Admin.
    def get_full_name(self) -> str:
        return self.nome_completo

    def get_short_name(self) -> str:
        return self.nome_completo.split(" ", 1)[0]
