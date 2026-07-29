SELECT s.ssObjectId, o.mpc_orb_jsonb FROM dp2.SSObject AS s JOIN dp2.mpc_orbits AS o ON s.designation = o.designation LIMIT 10;
