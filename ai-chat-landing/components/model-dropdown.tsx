"use client"

import { Check, ChevronDown, Cpu, Info } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MODEL_OPTIONS, optionById, type ModelId } from "@/lib/models/options"

/**
 * "AI LLM" single-select drop-down (spec 025, FR-001/FR-006 + grouped-menu
 * mockup): Local and Cloud sections with info tooltips, full model names,
 * a checkmark on the active entry. Every listed model is actually selectable
 * (all are wired in the chatflow); Local disables when unreachable (FR-004).
 */
export function ModelDropdown({
  value,
  localAvailable,
  onValueChange,
  onOpen,
}: {
  value: ModelId
  localAvailable: boolean
  onValueChange: (id: ModelId) => void
  onOpen: () => void
}) {
  const local = MODEL_OPTIONS.find((o) => o.origin === "local")!
  const cloud = MODEL_OPTIONS.filter((o) => o.origin === "cloud")
  return (
    <DropdownMenu
      onOpenChange={(open) => {
        if (open) onOpen()
      }}
    >
      <DropdownMenuTrigger
        render={
          <Button
            variant="ghost"
            size="sm"
            className="h-7 max-w-56 gap-1 px-2 text-xs font-medium text-muted-foreground"
            aria-label="AI LLM model selector"
          />
        }
      >
        <Cpu className="size-3.5 shrink-0" aria-hidden="true" />
        <span className="truncate">{optionById(value).displayName}</span>
        <ChevronDown className="size-3.5 shrink-0" aria-hidden="true" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="top" className="w-72">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            Local
            <span title="Runs on this host's CPU — private, slower" className="inline-flex">
              <Info className="size-3" aria-hidden="true" />
            </span>
          </DropdownMenuLabel>
          <DropdownMenuItem
            disabled={!localAvailable}
            onClick={() => onValueChange(local.id)}
          >
            <div className="min-w-0 flex-1">
              <div className="text-sm">{local.displayName}</div>
              {local.hint && (
                <div className="text-xs font-normal text-muted-foreground">
                  {local.hint}
                </div>
              )}
            </div>
            {value === local.id && <Check className="ml-2 size-4" aria-hidden="true" />}
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuLabel className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            Cloud
            <span title="Hosted provider — faster, requests leave the network" className="inline-flex">
              <Info className="size-3" aria-hidden="true" />
            </span>
          </DropdownMenuLabel>
          {cloud.map((option) => (
            <DropdownMenuItem key={option.id} onClick={() => onValueChange(option.id)}>
              <div className="min-w-0 flex-1 text-sm">{option.displayName}</div>
              {value === option.id && <Check className="ml-2 size-4" aria-hidden="true" />}
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
        {!localAvailable && (
          <div className="px-2 py-1.5 text-xs text-muted-foreground">
            Local model unavailable
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
