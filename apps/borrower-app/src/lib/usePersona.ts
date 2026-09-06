import { useEffect, useState } from "react";
import { getActivePersona, type DevPersona } from "./api";

export function usePersona(): DevPersona {
  const [persona, setPersona] = useState<DevPersona>(getActivePersona);

  useEffect(() => {
    function handlePersonaChange(e: Event) {
      const customEvent = e as CustomEvent<DevPersona>;
      if (customEvent.detail) {
        setPersona(customEvent.detail);
      }
    }
    window.addEventListener("credittech_persona_changed", handlePersonaChange);
    return () => {
      window.removeEventListener("credittech_persona_changed", handlePersonaChange);
    };
  }, []);

  return persona;
}

export function isAllowed(role: string, requiredRoles: string[]): boolean {
  if (role === "ADMIN") return true;
  return requiredRoles.includes(role);
}
