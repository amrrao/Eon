import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

const PROTECTED_ROUTES = ["/home", "/profile", "/messages"]
const AUTH_ROUTES = ["/"]

export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data } = await supabase.auth.getClaims()

  const isProtected = PROTECTED_ROUTES.some(route =>
    request.nextUrl.pathname.startsWith(route)
  )
  const isAuthRoute = AUTH_ROUTES.includes(request.nextUrl.pathname)

  if (isProtected && !data) {
    return NextResponse.redirect(new URL("/", request.url))
  }

  if (isAuthRoute && data) {
    return NextResponse.redirect(new URL("/home", request.url))
  }

  return response
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}