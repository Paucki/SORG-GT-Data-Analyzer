import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const url = Deno.env.get("SUPABASE_URL")!;
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const anon = Deno.env.get("SUPABASE_ANON_KEY") || Deno.env.get("SUPABASE_PUBLISHABLE_KEY")!;
  const authHeader = req.headers.get("Authorization") || "";

  const userClient = createClient(url, anon, {
    global: { headers: { Authorization: authHeader } },
    auth: { persistSession: false },
  });
  const admin = createClient(url, service, { auth: { persistSession: false } });

  const { data: authData, error: authError } = await userClient.auth.getUser();
  if (authError || !authData.user) return json({ error: "Nicht angemeldet" }, 401);

  const callerId = authData.user.id;
  const { data: membership, error: membershipError } = await admin
    .from("team_members")
    .select("team_id,role")
    .eq("user_id", callerId)
    .limit(1)
    .maybeSingle();

  if (membershipError || !membership || membership.role !== "admin") {
    return json({ error: "Nur Administratoren dürfen Benutzer verwalten." }, 403);
  }

  const teamId = membership.team_id;
  const body = await req.json().catch(() => ({}));
  const action = String(body.action || "");

  if (action === "list") {
    const { data: members, error: membersError } = await admin
      .from("team_members")
      .select("user_id,role,created_at")
      .eq("team_id", teamId);
    if (membersError) return json({ error: membersError.message }, 400);

    const { data: listData, error: listError } = await admin.auth.admin.listUsers({ page: 1, perPage: 1000 });
    if (listError) return json({ error: listError.message }, 400);

    const { data: profiles, error: profilesError } = await admin
      .from("profiles")
      .select("id,username,display_name,first_name,last_name,phone,residence,team_role");
    if (profilesError) return json({ error: profilesError.message }, 400);

    const memberMap = new Map((members || []).map((m: any) => [m.user_id, m]));
    const profileMap = new Map((profiles || []).map((p: any) => [p.id, p]));
    const users = (listData.users || [])
      .filter((u: any) => memberMap.has(u.id))
      .map((u: any) => {
        const m: any = memberMap.get(u.id);
        const p: any = profileMap.get(u.id) || {};
        return {
          id: u.id,
          username: p.username || "",
          first_name: p.first_name || "",
          last_name: p.last_name || "",
          display_name: p.display_name || [p.first_name,p.last_name].filter(Boolean).join(" ") || p.username || "Benutzer",
          phone: p.phone || "",
          residence: p.residence || "",
          team_role: p.team_role || "Mechaniker",
          permission: m?.role || "user",
          inactive: !!u.banned_until && new Date(u.banned_until).getTime() > Date.now(),
          banned_until: u.banned_until || null,
          created_at: u.created_at,
          last_sign_in_at: u.last_sign_in_at || null,
        };
      });
    return json({ users, caller_id: callerId });
  }

  if (action === "create") {
    const username = String(body.username || "").trim();
    const password = String(body.password || "");
    const firstName = String(body.first_name || "").trim();
    const lastName = String(body.last_name || "").trim();
    const displayName = [firstName,lastName].filter(Boolean).join(" ").trim() || String(body.display_name || "").trim();
    const phone = String(body.phone || "").trim();
    const residence = String(body.residence || "").trim();
    const teamRole = ["Reifen","Mechaniker","Car Chief","Fahrer"].includes(String(body.team_role))
      ? String(body.team_role) : "Mechaniker";
    const permission = body.permission === "admin" ? "admin" : "user";

    if (username.length < 3 || password.length < 6) {
      return json({ error: "Benutzername muss mindestens 3 Zeichen und Passwort mindestens 6 Zeichen haben." }, 400);
    }

    const { data: existingProfile } = await admin
      .from("profiles")
      .select("id")
      .ilike("username", username)
      .maybeSingle();
    if (existingProfile) return json({ error: "Benutzername ist bereits vergeben." }, 400);

    const safe = username.toLowerCase().replace(/[^a-z0-9._-]/g, "-").replace(/-+/g, "-");
    const authEmail = safe + "+" + crypto.randomUUID().slice(0,8) + "@sorg-gt.local";

    const { data, error } = await admin.auth.admin.createUser({
      email: authEmail,
      password,
      email_confirm: true,
      user_metadata: { display_name: displayName || username },
    });
    if (error || !data.user) return json({ error: error?.message || "Benutzer konnte nicht angelegt werden." }, 400);

    const { error: memberInsert } = await admin
      .from("team_members")
      .upsert({ team_id: teamId, user_id: data.user.id, role: permission }, { onConflict: "team_id,user_id" });
    if (memberInsert) return json({ error: memberInsert.message }, 400);

    const { error: profileError } = await admin.from("profiles").upsert({
      id: data.user.id,
      username,
      first_name: firstName,
      last_name: lastName,
      display_name: displayName || username,
      phone,
      residence,
      team_role: teamRole,
      updated_at: new Date().toISOString(),
    });
    if (profileError) return json({ error: profileError.message }, 400);

    return json({ ok: true, user_id: data.user.id });
  }

  const targetId = String(body.user_id || "");
  if (!targetId) return json({ error: "Benutzer fehlt." }, 400);

  const { data: targetMembership } = await admin
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", targetId)
    .maybeSingle();
  if (!targetMembership) return json({ error: "Benutzer gehört nicht zu diesem Team." }, 404);

  if (action === "update_profile") {
    const username = String(body.username || "").trim();
    const firstName = String(body.first_name || "").trim();
    const lastName = String(body.last_name || "").trim();
    const displayName = [firstName,lastName].filter(Boolean).join(" ").trim() || String(body.display_name || "").trim();
    const phone = String(body.phone || "").trim();
    const residence = String(body.residence || "").trim();
    const teamRole = ["Reifen","Mechaniker","Car Chief","Fahrer"].includes(String(body.team_role))
      ? String(body.team_role) : "Mechaniker";
    if (username.length < 3) return json({ error: "Benutzername muss mindestens 3 Zeichen haben." }, 400);

    const { data: duplicate } = await admin
      .from("profiles")
      .select("id")
      .ilike("username", username)
      .neq("id", targetId)
      .maybeSingle();
    if (duplicate) return json({ error: "Benutzername ist bereits vergeben." }, 400);

    const { error } = await admin
      .from("profiles")
      .update({
        username,
        first_name: firstName,
        last_name: lastName,
        display_name: displayName || username,
        phone,
        residence,
        team_role: teamRole,
        updated_at: new Date().toISOString(),
      })
      .eq("id", targetId);
    return error ? json({ error: error.message }, 400) : json({ ok: true });
  }

  if (action === "set_password") {
    const password = String(body.password || "");
    if (password.length < 6) return json({ error: "Passwort muss mindestens 6 Zeichen haben." }, 400);
    const { error } = await admin.auth.admin.updateUserById(targetId, { password });
    return error ? json({ error: error.message }, 400) : json({ ok: true });
  }

  if (action === "set_active") {
    const active = body.active === true;
    if (!active && targetId === callerId) return json({ error: "Du kannst deinen eigenen Admin-Zugang nicht deaktivieren." }, 400);
    const { error } = await admin.auth.admin.updateUserById(targetId, {
      ban_duration: active ? "none" : "876000h",
    });
    return error ? json({ error: error.message }, 400) : json({ ok: true });
  }

  if (action === "set_role") {
    const role = body.role === "admin" ? "admin" : "user";
    if (targetId === callerId && role !== "admin") return json({ error: "Du kannst dir selbst die Admin-Rechte nicht entziehen." }, 400);
    const { error } = await admin
      .from("team_members")
      .update({ role })
      .eq("team_id", teamId)
      .eq("user_id", targetId);
    return error ? json({ error: error.message }, 400) : json({ ok: true });
  }

  return json({ error: "Unbekannte Aktion." }, 400);
});
