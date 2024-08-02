from flask import url_for, render_template
from CTFd.models import UserTokens
from CTFd.utils import get_config
from CTFd.utils.helpers import get_infos, markup
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user

from ..models import Dojos, SSHKeys, DojoMembers
from ..utils.kook import get_kook_user


@authed_only
def settings_override():
    infos = get_infos()

    user = get_current_user()
    tokens = UserTokens.query.filter_by(user_id=user.id).all()

    ssh_key = SSHKeys.query.filter_by(user_id=user.id).first()
    ssh_key = ssh_key.value if ssh_key else None

    kook_user = get_kook_user(user.id)

    prevent_name_change = get_config("prevent_name_change")

    if get_config("verify_emails") and not user.verified:
        confirm_url = markup(url_for("auth.confirm"))
        infos.append(
            markup(
                "Your email address isn't confirmed!<br>"
                "Please check your email to confirm your email address.<br><br>"
                f'To have the confirmation email resent please <a href="{confirm_url}">click here</a>.'
            )
        )

    return render_template(
        "settings.html",
        user=user,
        tokens=tokens,
        ssh_key=ssh_key,
        prevent_name_change=prevent_name_change,
        infos=infos,
        kook_user=kook_user,
    )
