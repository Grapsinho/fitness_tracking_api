def set_jwt_cookie(response, access_token, refresh_token):
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=True,  # Ensures the cookie is sent only over HTTPS
        samesite='Strict'  # Prevents cross-site cookie sharing
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite='Strict'
    )
    return response