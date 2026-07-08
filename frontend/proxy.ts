import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const token = request.cookies.get('token')?.value
  const { pathname } = request.nextUrl

  const isAuthPage = pathname === '/login' || pathname === '/recuperar-password'
  const isPublic = pathname.startsWith('/_next') || pathname === '/favicon.ico'

  if (isPublic) return NextResponse.next()

  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  if (!isAuthPage && !token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
