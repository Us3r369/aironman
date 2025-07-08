# Run this once to make the setup script executable
chmod +x setup_env.sh

# Then set up your dev environment
./setup_env.sh

# AIronman Coaching App

## Garmin Connect Authentication Tokens

This app assumes you have previously run the example script from the [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) repository and have valid authentication token files saved in your home directory under `~/.garminconnect` (specifically, `oauth1_token.json` and `oauth2_token.json`).

**If you have not done this yet:**
1. Clone and run the example script from the python-garminconnect repo locally to generate your tokens.
2. The first run will prompt for your Garmin credentials and (if needed) MFA code. The tokens will be saved for future use.

## Using Tokens in Docker

To use your local tokens in the Docker container:
1. Mount your local `~/.garminconnect` directory into the container by adding this to your `docker-compose.yml` under the `backend` service:
   ```yaml
   volumes:
     - ~/.garminconnect:/app/.garmin_tokens
   ```
2. Set the following in your `.env` file:
   ```
   GARMINTOKENS=/app/.garmin_tokens
   ```

This will allow the app to authenticate with Garmin Connect using your existing tokens, avoiding the need to re-authenticate or enter MFA in the container.
