export function Footer() {
  return (
    <footer className="border-t bg-muted/30 py-6 md:py-8">
      <div className="container mx-auto px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-6xl mx-auto">
          <div className="space-y-3">
            <h4 className="text-base font-medium">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:underline">About Us</a></li>
              <li><a href="#" className="hover:underline">Careers</a></li>
              <li><a href="#" className="hover:underline">Contact</a></li>
              <li><a href="#" className="hover:underline">Blog</a></li>
            </ul>
          </div>
          <div className="space-y-3">
            <h4 className="text-base font-medium">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:underline">Property Guides</a></li>
              <li><a href="#" className="hover:underline">Area Information</a></li>
              <li><a href="#" className="hover:underline">Help Center</a></li>
              <li><a href="#" className="hover:underline">Site Map</a></li>
            </ul>
          </div>
          <div className="space-y-3">
            <h4 className="text-base font-medium">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:underline">Terms of Service</a></li>
              <li><a href="#" className="hover:underline">Privacy Policy</a></li>
              <li><a href="#" className="hover:underline">Cookie Policy</a></li>
              <li><a href="#" className="hover:underline">POPIA Compliance</a></li>
            </ul>
          </div>
          <div className="space-y-3">
            <h4 className="text-base font-medium">Connect</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:underline">Facebook</a></li>
              <li><a href="#" className="hover:underline">Twitter</a></li>
              <li><a href="#" className="hover:underline">Instagram</a></li>
              <li><a href="#" className="hover:underline">LinkedIn</a></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t text-center text-sm text-muted-foreground max-w-6xl mx-auto">
          <p>© 2025 PropMatch. All rights reserved.</p>
          <p className="mt-1">All properties displayed are examples for demonstration purposes only.</p>
        </div>
      </div>
    </footer>
  )
}