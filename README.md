# Gatekeeper
A discord back that lets you add someoen to black list with a message on why they have been added.




### Setup

1. Database Setup (Supabase)
Create a free project at Supabase.com.

Go to the SQL Editor tab in your Supabase dashboard and run this script to set up your tables:

```
-- Per-Server Whitelist
CREATE TABLE IF NOT EXISTS server_whitelist (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (guild_id, user_id)
);

-- Global Blacklist (Guild ID removed so bans apply network-wide)
CREATE TABLE IF NOT EXISTS global_blacklist (
    user_id BIGINT PRIMARY KEY,
    reason TEXT DEFAULT 'No reason provided',
    blacklisted_by BIGINT,
    added_at TIMESTAMPTZ DEFAULT NOW()
);
-- Server Configuration Table (Stores log channels per guild)
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    log_channel_id BIGINT
);

```