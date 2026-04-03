from __future__ import annotations

from typing import Dict, List

from flask_login import current_user

from src.models import RolePermission, UserPermissionOverride


# Processos principais do sistema para controle por papel.
PERMISSION_CATALOG: List[Dict[str, str]] = [
    {"key": "dashboard", "label": "Dashboard", "group": "Geral"},
    {"key": "entidades", "label": "Cadastro de Entidades", "group": "Cadastros"},
    {"key": "fluxo", "label": "Fluxo de Caixa", "group": "Cadastros"},
    {"key": "contas_banco", "label": "Contas Banco", "group": "Cadastros"},
    {"key": "lancamentos", "label": "Lançamentos", "group": "Movimentação"},
    {"key": "comissoes", "label": "Comissões", "group": "Processos"},
    {"key": "relatorios", "label": "Relatórios", "group": "Processos"},
    {"key": "importar_nfse", "label": "Importação NFSe", "group": "Importação"},
    {"key": "importar_ofx", "label": "Importação OFX", "group": "Importação"},
    {"key": "conciliacao", "label": "Conciliação Bancária", "group": "Importação"},
]

EDITABLE_ROLES = ("operator",)

# Admin sempre tem acesso total; operator/viewer podem ser ajustados na tela.
DEFAULT_ROLE_PERMISSIONS = {
    "operator": set(),
    "viewer": {
        "dashboard",
        "entidades",
        "fluxo",
        "contas_banco",
        "lancamentos",
        "comissoes",
        "relatorios",
        "importar_nfse",
        "importar_ofx",
        "conciliacao",
    },
}


def _resolve_user_role(user) -> str:
    if not user:
        return "viewer"
    if getattr(user, "is_admin", False):
        return "admin"
    return (getattr(user, "role", "viewer") or "viewer").strip().lower()


def has_permission_key(user, permission_key: str) -> bool:
    role = _resolve_user_role(user)
    if role == "admin":
        return True

    if not permission_key:
        return False

    empresa_id = getattr(user, "empresa_id", None)
    if not empresa_id:
        return False

    user_override = UserPermissionOverride.query.filter_by(
        empresa_id=empresa_id,
        user_id=getattr(user, "id", None),
        permission_key=permission_key,
    ).first()
    if user_override is not None:
        return bool(user_override.allowed)

    override = RolePermission.query.filter_by(
        empresa_id=empresa_id,
        role=role,
        permission_key=permission_key,
    ).first()
    if override is not None:
        return bool(override.allowed)

    return permission_key in DEFAULT_ROLE_PERMISSIONS.get(role, set())


def current_user_has_permission(permission_key: str) -> bool:
    return has_permission_key(current_user, permission_key)


def build_permissions_matrix(empresa_id: int) -> Dict[str, Dict[str, bool]]:
    matrix: Dict[str, Dict[str, bool]] = {
        key: {
            "admin": True,
            "operator": key in DEFAULT_ROLE_PERMISSIONS["operator"],
            "viewer": key in DEFAULT_ROLE_PERMISSIONS["viewer"],
        }
        for key in [item["key"] for item in PERMISSION_CATALOG]
    }

    overrides = RolePermission.query.filter_by(empresa_id=empresa_id).all()
    for item in overrides:
        if item.permission_key in matrix and item.role in matrix[item.permission_key]:
            matrix[item.permission_key][item.role] = bool(item.allowed)

    return matrix


def build_operator_permissions(empresa_id: int) -> Dict[str, bool]:
    matrix = build_permissions_matrix(empresa_id)
    return {key: matrix[key]["operator"] for key in matrix}


def save_permissions_matrix(empresa_id: int, form_data):
    keys = [item["key"] for item in PERMISSION_CATALOG]
    for role in EDITABLE_ROLES:
        for key in keys:
            checkbox_name = f"perm__{role}__{key}"
            allowed = checkbox_name in form_data

            entry = RolePermission.query.filter_by(
                empresa_id=empresa_id,
                role=role,
                permission_key=key,
            ).first()

            if entry is None:
                entry = RolePermission(
                    empresa_id=empresa_id,
                    role=role,
                    permission_key=key,
                    allowed=allowed,
                )
                RolePermission.query.session.add(entry)
            else:
                entry.allowed = allowed


def save_operator_permissions(empresa_id: int, form_data):
    keys = [item["key"] for item in PERMISSION_CATALOG]
    role = "operator"
    for key in keys:
        checkbox_name = f"perm__{role}__{key}"
        allowed = checkbox_name in form_data

        entry = RolePermission.query.filter_by(
            empresa_id=empresa_id,
            role=role,
            permission_key=key,
        ).first()

        if entry is None:
            entry = RolePermission(
                empresa_id=empresa_id,
                role=role,
                permission_key=key,
                allowed=allowed,
            )
            RolePermission.query.session.add(entry)
        else:
            entry.allowed = allowed


def build_user_overrides_matrix(empresa_id: int, user_id: int, role: str) -> Dict[str, str]:
    role = (role or "viewer").strip().lower()
    base = DEFAULT_ROLE_PERMISSIONS.get(role, set())
    matrix: Dict[str, str] = {}
    for item in PERMISSION_CATALOG:
        matrix[item["key"]] = "inherit_allow" if item["key"] in base else "inherit_deny"

    overrides = UserPermissionOverride.query.filter_by(
        empresa_id=empresa_id,
        user_id=user_id,
    ).all()
    for override in overrides:
        matrix[override.permission_key] = "allow" if override.allowed else "deny"

    return matrix


def save_user_overrides(empresa_id: int, user_id: int, form_data):
    keys = [item["key"] for item in PERMISSION_CATALOG]
    for key in keys:
        field_name = f"userperm__{key}"
        mode = (form_data.get(field_name) or "inherit").strip().lower()

        existing = UserPermissionOverride.query.filter_by(
            empresa_id=empresa_id,
            user_id=user_id,
            permission_key=key,
        ).first()

        if mode == "inherit":
            if existing is not None:
                UserPermissionOverride.query.session.delete(existing)
            continue

        allowed = mode == "allow"
        if existing is None:
            existing = UserPermissionOverride(
                empresa_id=empresa_id,
                user_id=user_id,
                permission_key=key,
                allowed=allowed,
            )
            UserPermissionOverride.query.session.add(existing)
        else:
            existing.allowed = allowed
