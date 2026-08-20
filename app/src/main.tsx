import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router-dom"
import { Toaster } from "sonner"

import { TooltipProvider } from "@/components/ui/tooltip"
import { OperationProvider } from "@/lib/operation-provider"

import App from "./App"
import "./index.css"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <OperationProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
          <Toaster position="bottom-center" richColors closeButton />
        </OperationProvider>
      </TooltipProvider>
    </QueryClientProvider>
  </StrictMode>,
)
